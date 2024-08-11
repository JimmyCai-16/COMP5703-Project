import colorsys
import concurrent
import json
from abc import ABC
from datetime import timedelta
from enum import Enum

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point, Polygon

from django.contrib.gis.serializers.geojson import Serializer
from django.db.models import Min, Max
from django.db.models.fields.related import RelatedField
from django.db.models.fields.related_descriptors import ForwardOneToOneDescriptor, ForwardManyToOneDescriptor
from django.http import JsonResponse


def map_api_endpoint():
    """Handles generic incoming data from the frontend e.g., bounding box."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):

            body = json.loads(request.body)

            # Get the bounding box
            north_east = body.get('northEast', None)
            south_west = body.get('southWest', None)

            if north_east and south_west:
                kwargs['bounding_box'] = get_bounding_box(north_east, south_west)

            # Call the view function
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def get_bounding_box(north_east, south_west):
    """Create a bounding box polygon from north-east and south-west coordinates.

    Parameters
    ----------
    north_east : dict
        Dictionary containing 'lat' and 'lng' keys for north-east corner.
    south_west : dict
        Dictionary containing 'lat' and 'lng' keys for south-west corner.

    Returns
    -------
    Polygon
        A Polygon representing the bounding box defined by the input coordinates.
    """
    # Create Point objects for the bounding coordinates
    ne_point = Point(north_east['lng'], north_east['lat'])
    sw_point = Point(south_west['lng'], south_west['lat'])

    # Create a bounding box polygon using the four corners
    bounding_box = Polygon.from_bbox((sw_point.x, sw_point.y, ne_point.x, ne_point.y))

    return bounding_box


def get_field_unique_values(queryset, field):
    """Returns the possible values for a specific field within a queryset. Ideally you shouldn't use this on fields
    expected to have large numbers of unique values e.g., dates or primary keys."""
    return queryset.values_list(field, flat=True).order_by(field).distinct()


def get_meta_choices_map(model, field):
    """Returns the choice map (key, value) for a specified field of a model."""
    return {key: value for key, value in model._meta.get_field(field).flatchoices}


def get_meta_choices_display(model, field):
    """Returns the values for a choice field. """
    return [value for key, value in model._meta.get_field(field).flatchoices]


def get_min_max(queryset, field):
    """Returns the minimum and maximum possible values for a field of a queryset."""
    result = queryset.aggregate(__min=Min(field), __max=Max(field))
    min_value = result.get('__min', None)
    max_value = result.get('__max', None)
    return min_value, max_value


def get_date_intervals(min_date, max_date, n=0, **kwargs) -> list:
    """Generates a list dates between a min and max date where the interval is based on timedelta (use kwargs). Number
    of dates is limited to N if N > 0.

    Parameters
    ----------
    min_date : datetime
    max_date : datetime
    n : int
        Number of intervals (only if above 0)
    kwargs
        Inputs to the timedelta e.g., days=365, years=5
    """
    i = 0
    interval = timedelta(**kwargs)

    intervals = []
    current_interval = max_date

    while current_interval > min_date and 0 >= n or n > i:
        intervals.append(current_interval)
        current_interval -= interval
        i += 1

    if n > 0:
        intervals.append(min_date)

    return intervals


def generate_date_segments(min_date, max_date, max_segments=5, days_per_segment=365) -> list:
    """Generates a list of date segment. Small differences will result in less than intended segments. Days past the max
    number of segments will be combined into the final segment.

    Parameters
    ----------
    min_date : datetime
    max_date : datetime
    max_segments : int
        Max number of segments allowed
    days_per_segment : int
        Number of days between each segment
    """
    difference = max_date - min_date
    years = difference.days / 365.25  # Taking into account leap years
    n_segments = min(int(years) + 1, max_segments)  # Max of 5 segments

    return get_date_intervals(min_date, max_date, n=n_segments, days=days_per_segment)


def generate_date_range_geojson(queryset, date_field, colour_map='hsv', segments=5, days_per_segment=365, serializer=None):
    """Generates a date tree from a queryset based on the date field. Default colour map is HSV.

    Parameters
    ----------
    queryset : QuerySet
    date_field : str
        Name of date field
    colour_map : str
        Colour map to use for branch
    segments : int
        Max number of dates segments
    days_per_segment : int
        Number of days between segments
    serializer : func[GeoJSONSerializer]
        Function used to serialize the queryset. Must return some GeoJSON like object.
    """
    # Generate the ranges for the date tree
    min_date, max_date = get_min_max(queryset, date_field)

    if not min_date or not max_date:
        return None

    # Prepare colour and date segments
    date_segments = generate_date_segments(min_date, max_date, max_segments=segments, days_per_segment=days_per_segment)
    date_colours = ColourMap.create_gradient(colour_map, n=len(date_segments))

    # Loop the date segments and generate the geojson for each layer
    branch = []
    for i, (min_date, max_date) in enumerate(zip(date_segments[1:], date_segments)):
        # Generate the geojson for each segment
        query_dict = {f"{date_field}__range": (min_date, max_date)}
        date_queryset = queryset.filter(**query_dict)

        if not date_queryset.exists():
            continue

        geojson = serializer(date_queryset).as_geojson()

        # Append the date leaf node to the status branch
        branch.append({
            'field': date_field,
            'value': i,
            'colour': date_colours[i],
            'display': f"{max_date} - {min_date}",
            'data': geojson
        })

    return branch


# class BaseGeoJSONSerializer(Serializer):
#     """
#     A serializer for converting Django model objects into JSON format with additional customization options.
#
#     Methods
#     -------
#     serialize(queryset, *args, **kwargs)
#         Serialize a queryset of model objects into JSON format with additional customization options such as display fields and custom functions.
#     """
#     model = None
#
#     def __init__(self):
#         self._properties = []
#         self._display = {}
#         self._funcs = {}
#         self._related_fields = []
#
#         super().__init__()
#
#     def end_object(self, obj):
#
#         for field in self._properties:
#             self._current[field] = getattr(obj, field)
#
#         for field, func in self._display.items():
#             self._current[f'{field}_display'] = func(obj)
#
#         for field, func in self._funcs.items():
#             self._current[field] = func(obj)
#
#         for model_func_tree in self._related_fields:
#             value, attr = obj, None
#
#             for func in model_func_tree:
#                 value, attr = func(value)
#
#             self._current[attr] = value
#
#         super().end_object(obj)
#
#     def serialize(self, queryset, *args, **kwargs):
#         """Serialize a QuerySet including properties and the result of object functions."""
#         self.model = queryset.model
#
#         # Filter out the properties
#         for field in kwargs.pop('properties', []):
#             field_attr = getattr(self.model, field)
#
#             if not field_attr:
#                 raise AttributeError(f"Invalid Attribute {field} for object {self.model}")
#
#             self._properties.append(field)
#
#         # Get the display functions
#         for field in kwargs.pop('display', []):
#             field_display = f'get_{field}_display'
#             field_attr = getattr(self.model, field_display)
#
#             if field_attr and callable(field_attr):
#                 self._display[field] = getattr(self.model, field_display)
#
#         # Get the functions
#         for field in kwargs.pop('funcs', []):
#             field_attr = getattr(self.model, field)
#
#             if field_attr and callable(field_attr):
#                 self._funcs[field] = field_attr
#
#         # Handle related fields
#         for field in kwargs.pop('related_fields', []):
#             split_field = field.split('__')
#
#             if len(split_field):
#                 raise ValueError("Related fields should include related property")
#
#             model_func_tree = []
#             current_model = queryset.model
#
#             for split in split_field:
#                 field_attr = getattr(current_model, split)
#
#                 # Define specific function to get the attribute from the current model
#                 model_func_tree.append(lambda e, attr=split: getattr(e, attr))
#
#                 # Update the current model to continue to fetch fields
#                 if isinstance(field_attr, ForwardOneToOneDescriptor):
#                     current_model = current_model._meta.get_field(split).related_model
#
#             # Append our model func tree
#             self._related_fields.append(model_func_tree)
#
#         return super().serialize(queryset, *args, **kwargs)
#
#
# class GeoJSONSerializer:
#     """
#     Serializes a queryset of models into GeoJSON format.
#
#     Parameters
#     ----------
#     queryset : QuerySet
#         A queryset of models to be serialized.
#     geometry_field : str
#         The name of the geometry field in the model.
#     fields : list of str
#         A list of field names to include for each feature.
#     funcs : list of callable, optional
#         A list of functions to apply to the queryset (default is None).
#     display : list of str, optional
#         A list of fields to display (e.g., `some_field` will return `get_some_field_display()`).
#
#     Attributes
#     ----------
#     geometry_field : str
#         The name of the geometry field in the model.
#     fields : list[str]
#         Model fields/properties to be serialized.
#     funcs : list of callable
#         Model functions to be serialized (will return the results).
#     display : list of str
#         Model fields with a `get_field_display()` function attached. Serialized as `field_display`
#     queryset : QuerySet
#         The queryset of models to be serialized.
#
#     Methods
#     -------
#     as_geojson()
#         Serialize the queryset to GeoJSON format.
#
#     as_response()
#         Return the GeoJSON as a JsonResponse.
#     """
#
#     def __init__(self, queryset, geometry_field: str, fields: list, properties=None, funcs=None, display=None, related_fields=None):
#         if display is None:
#             display = []
#         if funcs is None:
#             funcs = []
#         if properties is None:
#             properties = []
#         if related_fields is None:
#             related_fields = []
#
#         self.queryset = queryset
#         self.geometry_field = geometry_field
#         self.fields = fields
#         self.properties = properties
#         self.funcs = funcs
#         self.display = display
#         self.related_fields = related_fields
#
#     def as_geojson(self, **options):
#         """
#         Serialize the queryset to GeoJSON format.
#
#         Returns
#         -------
#         dict
#             The serialized GeoJSON.
#         """
#         return BaseGeoJSONSerializer().serialize(
#             self.queryset,
#             geometry_field=self.geometry_field,
#             properties=self.properties,
#             fields=self.fields,
#             funcs=self.funcs,
#             display=self.display,
#             related_fields=self.related_fields,
#             **options
#         )
#
#     def as_response(self):
#         """
#         Return the GeoJSON as a JsonResponse.
#
#         Returns
#         -------
#         JsonResponse
#             A JsonResponse containing the GeoJSON data.
#         """
#         return JsonResponse(self.as_geojson(), safe=False)


def queryset_to_dict_array(queryset, related_fields=None):
    """
    Converts a queryset to an array of dictionaries with specified related fields.

    Args:
        queryset (QuerySet): The queryset to convert.
        related_fields (list, optional): List of related fields to include.

    Returns:
        list: Array of dictionaries with specified fields.
    """
    if related_fields is None:
        related_fields = []

    result_array = []
    for obj in queryset:
        obj_dict = {field: getattr(obj, field) for field in obj._meta.get_fields()}
        for related_field in related_fields:
            related_model, field_name = related_field.split('.')
            related_value = getattr(obj, related_model).__dict__.get(field_name)
            obj_dict[related_field] = related_value
        result_array.append(obj_dict)

    return result_array


class ColourMap(Enum):
    """Various colour maps. Base colours come in list format.
    Use the cmap or rcmap to return a matplotlib ListedColormap.
    """
    # TODO: Check that the colours are actually correct, these were generated by ChatGPT
    BROWN = ['#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F4A460']
    ORANGE = ['#FF4500', '#FF6347', '#FF7F50', '#FFA500', '#FFD700']
    PURPLE = ['#800080', '#8A2BE2', '#9932CC', '#BA55D3', '#DA70D6']
    CYAN = ['#008B8B', '#00BFFF', '#00CED1', '#20B2AA', '#40E0D0']
    MAGENTA = ['#8A2BE2', '#9400D3', '#9932CC', '#BA55D3', '#DA70D6']
    YELLOW = ['#FFD700', '#FFDA44', '#FFDF87', '#FFE5CA', '#FFEBFD']
    PINK = ['#FF1493', '#FF4081', '#FF69B4', '#FF91A4', '#FFC0CB']
    TEAL = ['#008080', '#2E8B57', '#48D1CC', '#66CDAA', '#7FFFD4']
    LAVENDER = ['#E6E6FA', '#D8BFD8', '#DDA0DD', '#EE82EE', '#FF00FF']
    OLIVE = ['#6B8E23', '#808000', '#808033', '#808066', '#808099']
    MAROON = ['#800000', '#8A0000', '#940000', '#9E0000', '#A52A2A']
    NAVY = ['#000080', '#00008B', '#0000CD', '#0000FF', '#1E90FF']
    SALMON = ['#FF4500', '#FF6347', '#FF7F50', '#FFA07A', '#FFDAB9']
    GOLD = ['#FFD700', '#FFDB58', '#FFDC82', '#FFDDA0', '#FFDEAD']
    INDIGO = ['#4B0082', '#483D8B', '#473C8B', '#3A36A1', '#2E37AE']
    PEACH = ['#FFDAB9', '#FFDAB9', '#FFDAB9', '#FFDAB9', '#FFDAB9']
    LIME = ['#00FF00', '#32CD32', '#7FFF00', '#ADFF2F', '#DFFF00']
    PERU = ['#CD853F', '#8B4513', '#A0522D', '#D2691E', '#795548']
    ORCHID = ['#9932CC', '#8A2BE2', '#9400D3', '#BA55D3', '#DA70D6']
    SLATEBLUE = ['#4B0082', '#483D8B', '#7A67EE', '#836FFF', '#6A5ACD']

    # Primary Colours
    RED = ['#FF0000', '#FF3300', '#FF6600', '#FF9900', '#FFCC00']
    GREEN = ['#006600', '#008000', '#00B300', '#00E600', '#00FF00']
    BLUE = ['#0000FF', '#0033FF', '#0066FF', '#0099FF', '#00CCFF']
    GRAY = ['#808080', '#A0A0A0', '#C0C0C0', '#D3D3D3', '#F0F0F0']
    BLACK = ['#000000', '#202020', '#404040', '#606060', '#808080']

    @staticmethod
    def get_cmap(name, lut=None):
        """Returns a built-in matplotlib colour map using plt.cm.get_cmap"""
        return plt.cm.get_cmap(name, lut)

    @staticmethod
    def create_colormap(*hex_colours):
        """Creates a colourmap from an iterable of hex colours."""
        # Convert HEX colors to RGBA
        color_rgba = [mcolors.hex2color(hex_color) for hex_color in hex_colours]

        # Create a custom colormap
        return mcolors.ListedColormap(color_rgba)

    @staticmethod
    def create_gradient(colour_map, n):
        """Generates an N length colour gradient list from an input colour map."""
        norm = mcolors.Normalize(vmin=0, vmax=n - 1)

        gradient = []
        for step in range(n):
            color = colour_map(norm(step))
            gradient.append(color)

        return gradient

    @property
    def cmap(self):
        """Returns a matplotlib ListedColormap"""
        return self.create_colormap(*self.value)

    @property
    def rcmap(self):
        """Returns a reversed Matplotlib ListedColormap"""
        return self.create_colormap(*self.value[::-1])

    def get_gradient(self, n=5):
        """Generates an N length colour gradient list from the colour map"""
        return self.create_gradient(self.value, n)


class Colour(Enum):
    YELLOW = '#FFFF00'
    ORANGE = '#FFA500'
    PURPLE = '#800080'
    PINK = '#FFC0CB'
    BROWN = '#A52A2A'
    GRAY = '#808080'
    CYAN = '#008B8B'
    MAGENTA = '#8A2BE2'
    TEAL = '#008080'
    LAVENDER = '#E6E6FA'
    OLIVE = '#6B8E23'
    MAROON = '#800000'
    NAVY = '#000080'
    SALMON = '#FF4500'
    GOLD = '#FFD700'
    INDIGO = '#4B0082'
    PEACH = '#FFDAB9'
    LIME = '#00FF00'
    PERU = '#CD853F'
    ORCHID = '#9932CC'
    SLATEBLUE = '#6A5ACD'
    FORESTGREEN = '#48C446'

    # Primary colours
    RED = '#FF0000'
    GREEN = '#00FF00'
    BLUE = '#0000FF'
    BLACK = '#000000'
    WHITE = '#FFFFFF'

    @property
    def rgba(self):
        return mcolors.to_rgba(self.value)

    @staticmethod
    def to_rgba(c, alpha=None):
        """Convert c to an RGBA color.

        Parameters
        ==========
        alpha : float
            If *alpha* is not ``None``, it forces the alpha value, except if *c* is ``"none"`` (case-insensitive), which always maps to ``(0, 0, 0, 0)``.

        Returns
        =======
        rgba : tuple
            Tuple of ``(r, g, b, a)`` scalars.
        """
        return mcolors.to_rgba(c, alpha=alpha)

    @staticmethod
    def from_string_hash(string):
        """Generates a colour from the hash of some input string."""
        # Calculate the hash value of the input string
        hash_value = hash(string)

        # Normalize the hash value to the range [0, 1]
        normalized_hash = (hash_value & 0xFFFFFFFF) / float(0xFFFFFFFF)

        # Convert the normalized hash value to RGB using the HSV color space
        hue = normalized_hash
        saturation = 0.8
        value = 0.9
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)

        return r, g, b, 1


def parallelize_function(function, parameter_lists):
    """
    Parallelize the execution of a single function with multiple sets of arguments and maintain the original order of results.

    Parameters
    ----------
    function : callable
        The function to be executed in parallel with different sets of arguments.
    parameter_lists : list
        A list of argument sets (each as a tuple) to be applied to the single function.

    Returns
    -------
    list
        A list of results from the executed function with different argument sets, maintaining the original order.

    Example
    -------
    >>> add_numbers = lambda x, y: x + y
    >>> number_lists = [(1, 2), (3, 4), (5, 6)]

    >>> sums = parallelize_functions(add_numbers, number_lists)
    >>> a, b, c = parallelize_functions(add_numbers, number_lists)
    """
    def perform_query(idx, args):
        is_iterable = True

        try:
            iter(args)
        except TypeError:
            is_iterable = False

        if is_iterable:
            return idx, function(*args, order=idx)
        else:
            return idx, function(args, order=idx)

    # Create a ThreadPoolExecutor to parallelize queries
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(parameter_lists)) as executor:
        futures = [executor.submit(perform_query, idx, args) for idx, args in enumerate(parameter_lists)]

        # Collect the results and maintain the original order
        results = [None] * len(futures)
        for future in concurrent.futures.as_completed(futures):
            idx, result = future.result()
            results[idx] = result

    return tuple(results)


def parallelize_functions(functions):
    """
    Parallelize the execution of a list of functions with arguments and maintain the original order of results.

    Parameters
    ----------
    functions : list
        A list of functions and their respective arguments to be executed in parallel.

    Returns
    -------
    list
        A list of results from the executed functions, maintaining the original order.

    Example
    -------
    functions = [
        (func1, arg1, arg2),
        (func2, arg3),
        (func3,),
    ]
    results = parallelize_functions(functions)
    """
    def _perform_query(idx, args):
        func, *func_args = args
        return idx, func(*func_args, order=idx)

    # Create a ThreadPoolExecutor to parallelize queries
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(functions)) as executor:
        futures = [executor.submit(_perform_query, idx, func_args) for idx, func_args in enumerate(functions)]

        # Collect the results and maintain the original order
        results = [None] * len(futures)
        for future in concurrent.futures.as_completed(futures):
            idx, result = future.result()
            results[idx] = result

    return tuple(results)
