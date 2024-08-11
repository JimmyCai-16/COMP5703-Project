import json
from datetime import datetime
from enum import Enum

import requests
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.serializers import geojson
from django.db.models.fields.related_descriptors import ForwardOneToOneDescriptor, ForwardManyToOneDescriptor
from typing import IO


class GeoJSONSerializer(geojson.Serializer):
    """Serializes Django Models including related models (excluding manytomany or onetomany), properties and functions."""
    _field_funcs = []
    _geometry_func = None
    _qs = None

    def __init__(self):
        self._field_funcs = []

    def _handle_func_tree(self, obj, tree):
        attr, value = None, obj

        for func in tree:
            try:
                attr, value = func(value)
            except AttributeError:
                raise

            # Get the value of `value` if it's a callable (e.g., function or property)
            if callable(value):
                value = value()

            # If the value is None, break this loop since there's no nodes after this one.
            if value is None:
                break

        # Format attribute name
        if attr.startswith('get_'):
            attr = attr[4:]

        return attr, value

    def _get_model_func_tree(self, field):
        split_field = field.split('__')

        model_func_tree = []
        current_model = self._qs.model  # For traversing the attribute tree

        # If the attribute doesn't exist maybe we want to do something
        if not hasattr(self._qs.model, field):
            pass

        # Iterate the split fields and action them appropriately
        for split in split_field:
            try:
                field_attr = getattr(current_model, split)
            except AttributeError:
                # Annotated/Aggregated fields won't show up as an attribute here, however, even when a bad name is
                # given, if the attribute truly doesn't exist, an error will be thrown later for it.
                field_attr = None

            # Define specific function to get the attribute from the current model
            field_func = lambda v, a=split: (a, getattr(v, a) if v else None)
            model_func_tree.append(field_func)

            # Update the current model to continue to fetch fields
            if isinstance(field_attr, (ForwardOneToOneDescriptor, ForwardManyToOneDescriptor)):
                current_model = current_model._meta.get_field(split).related_model

        return model_func_tree

    def end_object(self, obj):
        # Handle the geometry and function trees
        if self._geometry_func:
            _, value = self._handle_func_tree(obj, self._geometry_func)
            self._geometry = value

        for func_tree in self._field_funcs:
            key, value = self._handle_func_tree(obj, func_tree)
            self._current[key] = value

        return super().end_object(obj)

    def serialize(
            self,
            queryset,
            *args,
            fields=None,
            geometry_field='geom',
            use_natural_foreign_keys=False,
            use_natural_primary_keys=False,
            **options,
    ):
        """Serializes a queryset into a GeoJSON format.

        Parameters
        ----------
        queryset : QuerySet
            Objects to serialize
        fields : list[str]
            List of field, function, property and simple relationship fields.
        geometry_field : str
            Field in which the geometry exists, this can also be a related field.
        use_natural_primary_keys : bool
        use_natural_foreign_keys : bool
        **options

        See Also
        --------
        :class:`django.contrib.gis.serializers.geojson.Serializer` : For super class documentation

        Returns
        -------
        geojson : str
        """
        self._qs = queryset

        if '__' in geometry_field:
            self._geometry_func = self._get_model_func_tree(geometry_field)

        # Build func trees for the func fields
        for field in fields:
            model_func_tree = self._get_model_func_tree(field)

            self._field_funcs.append(model_func_tree)

        return super().serialize(
            queryset,
            *args,
            fields=fields,
            geometry_field=geometry_field,
            use_natural_foreign_keys=use_natural_foreign_keys,
            use_natural_primary_keys=use_natural_primary_keys,
            **options
        )

class ServerType(Enum):
    REST = 0
    WFS = 1
    JSON = 2

SERVER_TYPE_PARAMS = {
    ServerType.REST: {
        'where': '1=1',
        'geometryType': 'esriGeometryPolygon',
        'spatialRel': 'esriSpatialRelIntersects',
        'units': 'esriSRUnit_Meter',
        'returnGeodetic': False,
        'outFields': '*',
        'returnGeometry': True,
        'returnCentroid': False,
        'featureEncoding': 'esriDefault',
        'multipatchOption': 'xyFootprint',
        'applyVCSProjection': False,
        'returnIdsOnly': False,
        'returnUniqueIdsOnly': False,
        'returnCountOnly': False,
        'returnExtentOnly': False,
        'returnQueryGeometry': False,
        'returnDistinctValues': False,
        'cacheHint': False,
        'returnZ': False,
        'returnM': False,
        'returnExceededLimitFeatures': True,
        'sqlFormat': 'none',
        'f': 'geojson',

        'resultOffset': 0,
        'resultRecordCount': 1000,
    },
    ServerType.WFS: {},
    ServerType.JSON: {},
}

SERVER_TYPE_COUNT_PARAMS = {
    ServerType.REST: {
        'where': '1=1',
        'returnCountOnly': True,
        'f': 'json'
    },
    ServerType.WFS: {},
    ServerType.JSON: {},
}

def map_geojson(model, url, map_dict, unique_fields=list, geometry_field='geom', **kwargs):
    server_type = kwargs.get('server_type', ServerType.REST)

    extents = kwargs.get('extents', None)

    query_params = SERVER_TYPE_PARAMS[server_type]
    count_params = SERVER_TYPE_COUNT_PARAMS[server_type]
    total_record_count = 0

    if server_type == ServerType.REST:

        if extents:
            geometry_attributes = {
                'geometry': extents,
                'geometryType': 'esriGeometryEnvelope',
                'spatialRel': 'esriSpatialRelIntersects',
                'inSR': 4326,
            }
            count_params = {**count_params, **geometry_attributes}
            query_params = {**query_params, **geometry_attributes}

        # Get allowed number of items per query
        pjson = requests.get(url, {'f': 'pjson'}).json()
        records_per_query = pjson.get('maxRecordCount', 1000)

        query_params['resultRecordCount'] = records_per_query  # update query to limit #

        # Get total counts in DB
        count_request = requests.get(url + '/query', count_params)
        total_record_count = count_request.json().get('count', -1)

        if settings.DEBUG:
            print(url)
            print(f"[{datetime.now()}] Total Records: {total_record_count}, Records p/Query: {records_per_query}")

    elif server_type == ServerType.WFS:
        raise NotImplementedError("Cannot currently map WFS servers")

    elif server_type == ServerType.JSON:
        raise NotImplementedError("Cannot currently map JSON servers")

    def map_inner(_geo_json, position):

        if _geo_json:
            features = _geo_json.get("features", [])

            # Loop the features within the current block of geojson
            for feature in features:
                # Extract some data from the feature
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                mapped_properties = {}
                unique_properties = {}

                # Map the geometry
                mapped_properties[geometry_field] = GEOSGeometry(json.dumps(geometry))

                # Map the GeoJSON properties
                for key_to, (key_from, map_func) in map_dict.items():
                    value = properties.get(key_from)

                    if callable(map_func):
                        # We may need to use the geometry as a function argument
                        if key_from == "_geometry":
                            value = mapped_properties[geometry_field]

                        value = map_func(value)

                    if key_to in unique_fields:
                        unique_properties[key_to] = value
                    else:
                        mapped_properties[key_to] = value

                # Create/update our DB entry
                if unique_fields:
                    print(mapped_properties)
                    model.objects.update_or_create(**unique_properties, defaults=mapped_properties)
                else:
                    model.objects.create(**mapped_properties)

                position += 1

                if settings.DEBUG:
                    percent_complete = (position / total_record_count) * 100

                    print(f"[{datetime.now()}][{percent_complete:.02f}%] {position} of {total_record_count}",
                          end='\r')

        return position

    if server_type == ServerType.REST:

        while query_params["resultOffset"] < total_record_count:
            # Perform request
            record_request = requests.get(url + '/query', query_params)

            print(url)

            geo_json = record_request.json()

            # Map the json to database models and move to next page
            query_params["resultOffset"] = map_inner(geo_json, query_params["resultOffset"])

    elif server_type == ServerType.WFS:
        raise NotImplementedError("Cannot currently map WFS servers")

    elif server_type == ServerType.JSON:
        raise NotImplementedError("Cannot currently map JSON servers")
