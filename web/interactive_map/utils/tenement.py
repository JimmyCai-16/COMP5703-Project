import calendar
import concurrent
from datetime import date, timedelta

from django.db.models import Q, QuerySet, Count, Max, Min

from interactive_map.utils.core import get_field_unique_values, get_meta_choices_map, Colour, ColourMap, \
    generate_date_range_geojson, get_min_max, parallelize_function
from main.utils.geojson import GeoJSONSerializer
from tms.models import Tenement, Moratorium


def tenement_serializer(queryset) -> GeoJSONSerializer:
    """Standard serialization function for tenements"""
    if queryset.model != Tenement:
        raise ValueError(f"This queryset must be of type Tenement and not {queryset.model}")

    return GeoJSONSerializer().serialize(
        queryset,
        geometry_field="area_polygons",
        fields=[
            "permit_id", "permit_state", "permit_type", "permit_number", "permit_status", "date_lodged", "date_granted",
            "date_commenced", "date_expiry", "date_renewed", "ahr_name", "get_permit_status_display",
            "get_permit_type_display"
        ],
    )


def get_permit_state_choices(queryset):
    """Returns a tuple of all possible options for a queryset, and all possible options for a model."""
    return list(get_field_unique_values(queryset, 'permit_state')), get_meta_choices_map(Tenement, 'permit_state')


def get_permit_type_choices(queryset):
    """Returns a tuple of all possible options for a queryset, and all possible options for a model."""
    return list(get_field_unique_values(queryset, 'permit_type')), get_meta_choices_map(Tenement, 'permit_type')


def get_permit_status_choices(queryset):
    """Returns a tuple of all possible options for a queryset, and all possible options for a model."""
    return list(get_field_unique_values(queryset, 'permit_status')), get_meta_choices_map(Tenement, 'permit_status')


def basic_permit_tree(queryset):
    colours = {
        'EPM': Colour.MAGENTA.rgba,
        'MDL': Colour.PURPLE.rgba,
        'ML': Colour.ORANGE.rgba,
        'EPC': Colour.BLUE.rgba,
        'default': Colour.GRAY.rgba,
    }

    permit_types, permit_type_choice_map = get_permit_type_choices(queryset)

    queries = []
    for permit_type in permit_types:
        display = permit_type_choice_map.get(permit_type)
        queries.append((permit_type, display, Q(permit_type=permit_type)))

    def run_query(permit_type, permit_type_display, query, **kwargs):
        """Parallel query function"""
        queryset_split = queryset.filter(query)
        queryset_count = queryset_split.count()

        return {
            'value': permit_type,
            'colour': colours.get(permit_type),
            'display': f'{permit_type_display} ({queryset_count})',
            'enabled': True,
            'data': tenement_serializer(queryset_split),
        }

    # Run all the queries
    branch = parallelize_function(run_query, queries)

    return branch


def permit_type_status_tree(queryset):
    tree_options = {
        'EPM':
            {
                'G': {'field': 'date_granted', 'colour': Colour.PINK.rgba},
                'A': {'field': 'date_lodged', 'colour': Colour.CYAN.rgba},
                'N': {'field': 'date_expiry', 'colour': Colour.MAGENTA.rgba}
            },
        'MDL':
            {
                'G': {'field': 'date_granted', 'colour': Colour.RED.rgba},
                'A': {'field': 'date_lodged', 'colour': Colour.PERU.rgba},
                'N': {'field': 'date_expiry', 'colour': Colour.SLATEBLUE.rgba}
            },
        'ML':
            {
                'G': {'field': 'date_granted', 'colour': Colour.BLUE.rgba},
                'A': {'field': 'date_lodged', 'colour': Colour.GREEN.rgba},
                'N': {'field': 'date_expiry', 'colour': Colour.INDIGO.rgba}
            },
    }

    # Initial setup
    tree = []
    permit_types, permit_type_choice_map = get_permit_type_choices(queryset)
    permit_statuses, permit_status_choice_map = get_permit_status_choices(queryset)

    # Begin graph looping
    for permit_type in permit_types:
        permit_type_options = tree_options.get(permit_type, tree_options.get('default'))
        type_branch = {
            'field': 'permit_type',
            'display': permit_type_choice_map.get(permit_type) + f' ({permit_type})',
            'value': permit_type,
            'children': []
        }

        for permit_status in permit_statuses:
            permit_queryset = queryset.filter(permit_type=permit_type, permit_status=permit_status)
            permit_status_options = permit_type_options.get(permit_status, {})

            if not permit_queryset.exists():
                continue

            status_branch = {
                'field': 'permit_status',
                'display': permit_status_choice_map.get(permit_status) + f' ({len(permit_queryset)})',
                'value': permit_status,
                'colour': permit_status_options.get('colour', Colour.GRAY.rgba),
                'data': tenement_serializer(permit_queryset)
            }

            type_branch['children'].append(status_branch)

        tree.append(type_branch)

    return tree


def epm_pending_date_tree(queryset: QuerySet[Tenement], visible=False, **kwargs):
    """EPM Pending Applications with 5 Date-Filtering layers:

    1. Lodged within the year from current date: Year 1 (Red)
    2. Second Year from current date: Year 2 (Orange)
    3. Third Year from current date: Year 3 (Brown)
    4. Fourth Year from current date: Year 4 (Light Blue)
    5. Every tenement before that: Year 5 (Dark Blue)
    """
    # Set up date constants
    n_segments = kwargs.get('n_segments', 5)
    years_increment = kwargs.get('years_increment', 1)

    # Define the colour map for this specific layer
    colour_map = ColourMap.create_colormap('#4556C3', '#7B9FF9', '#A37D6A', '#EE8468', '#B81131').reversed()
    colours = ColourMap.create_gradient(colour_map, n=n_segments + 1)

    # Set up base queryset based on requirements
    base_queryset = queryset.filter(permit_type='EPM', permit_status='A').order_by('-date_lodged')
    base_count = base_queryset.count()

    # Prepare queries
    queries = []
    current_date = date.today()
    for i in range(n_segments - 1):
        # Get the end of this loop date
        is_leap_year = calendar.isleap(current_date.year)
        days_add = 365 + int(is_leap_year)
        end_date = current_date - timedelta(days=years_increment * days_add)

        # Split the queryset on date ranges
        queries.append((current_date, end_date, Q(date_lodged__gt=end_date, date_lodged__lte=current_date)))

        # Update current date to the end of this loop
        current_date = end_date

    # Add last query
    queries.append((current_date, None, Q(date_lodged__lte=current_date)))

    def run_query(date_a, date_b, query, order=None):
        """Parallel query function"""
        queryset_split = base_queryset.filter(query)
        queryset_count = queryset_split.count()

        return {
            'value': order,
            'colour': colours[order],
            'display': f'{date_a} - {date_b} ({queryset_count})' if date_b else f'Before {date_a}',
            'enabled': visible,
            'data': tenement_serializer(queryset_split),
        }

    # Run all the queries
    branch = parallelize_function(run_query, queries)

    return {
        'display': f'Lodged Permits ({base_count})',
        'value': 'A',
        'children': branch
    }


def epm_moratorium_date_tree(queryset: QuerySet[Moratorium], visible=False, **kwargs):
    """EPM Pending Applications with 5 Date-Filtering layers:

    1. Expired within one week before current date: Week 1 (Darkest Shade)
    2. Expired within 2 weeks before that: Week 2, 3
    3. Expired within next 2 weeks: Week 4, 5
    4. Expired within next 3 weeks: Week 6, 7, 8
    5. Expired before that: Week 9 and more (Lightest Shade)
    """
    # Set up date constants
    week_intervals = (1, 2, 2, 3)
    n_segments = len(week_intervals)
    current_date = date.today()

    # Define the colour map for this specific layer
    colour_map = ColourMap.PINK.cmap
    colours = ColourMap.create_gradient(colour_map, n=n_segments + 1)

    # Initial filter for EPM that have past expiry dates.
    # TODO: Need to account for applications under 'renewal' may need new to use field to keep track (not currently mapped)
    base_queryset = queryset
    base_count = queryset.count()

    # Prepare queries
    queries = []
    for i, week_interval in enumerate(week_intervals):
        # Get the end of this loop date
        days_add = 7 * week_interval
        end_date = current_date + timedelta(days=days_add)

        # Split the queryset on date ranges
        queries.append((current_date, end_date, Q(effective_date__lt=end_date, effective_date__gte=current_date)))

        # Update current date to the end of this loop
        current_date = end_date

    # Add last query
    queries.append((current_date, None, Q(effective_date__gte=current_date)))

    def run_query(date_a, date_b, query, order=None):
        """Parallel query function"""
        queryset_split = base_queryset.filter(query)
        queryset_count = queryset_split.count()

        return {
            'value': order,
            'colour': colours[order],
            'display': f'{date_a} - {date_b} ({queryset_count})' if date_b else f'After {date_a} ({queryset_count})',
            'enabled': visible,
            'data': GeoJSONSerializer().serialize(
                queryset_split,
                geometry_field='geom',
                fields=['effective_date', 'tenement__permit_id', 'tenement__permit_type', 'tenement__permit_number',
                        'tenement__permit_status'],
            ),
        }

    # Run all the queries
    branch = parallelize_function(run_query, queries)

    return {
        'display': f'Moratorium ({base_count})',
        'value': 'N',
        'children': branch
    }


def epm_granted_date_tree(queryset: QuerySet[Tenement],visible=False, **kwargs):
    """EPM Pending Applications with 5 Date-Filtering layers:

    6 Total bins, where each bin is a 6th of the total number of EPMs.
    Coloured by recently granted (light green) to the latest granted (dark green).
    """
    # Set up date constants
    n_segments = kwargs.get('n_segments', 6)
    current_date = date.today()

    # Define the colour map for this specific layer
    colour_map = ColourMap.GREEN.cmap.reversed()
    colours = ColourMap.create_gradient(colour_map, n=n_segments)

    # Perform base query for setup of the granted date tree.
    base_queryset = queryset.filter(
        permit_type='EPM',
        permit_status='G',
        date_granted__isnull=False,
        date_expiry__gt=current_date,
        date_expiry__isnull=False
    ).order_by('-date_granted')
    base_count = base_queryset.count()

    # Organize the chunk slices
    chunk_size = base_count // n_segments
    slices = []

    for chunk, chunk_start in enumerate(range(0, base_count - chunk_size, chunk_size)):
        if chunk != (n_segments - 1):
            chunk_slice = slice(chunk_start, chunk_start + chunk_size)
        else:
            chunk_slice = slice(chunk_start, None)

        slices.append(chunk_slice)

    def run_query(query_slice, order=None):
        queryset_split = base_queryset[query_slice]
        count = len(queryset_split)

        # Get the proper dates, where the first date is the granted date of the end of the previous chunk
        date_a = base_queryset[query_slice.start - 1].date_granted if query_slice.start else current_date

        # Minimum date of the target chunk (where minimum is further back in history)
        date_b = queryset_split.aggregate(date_b=Min('date_granted'))['date_b']

        return {
            'value': order,
            'colour': colours[order],
            'display': f'{date_a} - {date_b} ({count})' if query_slice.stop else f'Before {date_a} ({count})',
            'enabled': visible,
            'data': tenement_serializer(queryset_split),
        }

    # Create the branch with parallel queries because we perform multiple aggregations
    branch = parallelize_function(run_query, slices)

    # Add "approaching expiry" branch to the tree
    expiring_tree = tenements_expiring_tree(queryset, 'EPM', 'G', Colour.YELLOW)
    branch = list(branch) + [expiring_tree]

    return {
        'display': f'Granted Permits ({base_count})',
        'value': 'G',
        'children': branch
    }

def tenements_expiring_tree(queryset, permit_type, permit_status, colour: Colour, visible=False, **kwargs):
    current_date = date.today()
    six_months_from_now = current_date + timedelta(days=180)  # Assuming 6 months = 180 days

    tenement_queryset = queryset.filter(
        permit_type=permit_type,
        permit_status=permit_status,
        date_expiry__gte=current_date,
        date_expiry__lte=six_months_from_now
    )
    queryset_count = tenement_queryset.count()

    return {
        'display': f'Approaching Expiry ({queryset_count})',
        'value': f'{permit_status}_expiring',
        'colour': colour.rgba,
        'enabled': visible,
        'data': tenement_serializer(tenement_queryset)
    }


def tenement_moratorium(queryset):
    queryset = Moratorium.objects.all()
    queryset_count = queryset.count()

    serialized_data = GeoJSONSerializer().serialize(
        queryset,
        geometry_field='geom',
        fields=['effective_date', 'tenement__permit_id', 'tenement__permit_type', 'tenement__permit_number', 'tenement__permit_status'],
    )

    return {
        'display': f'Moratorium ({queryset_count})',
        'value': 'moratorium',
        'colour': Colour.BLACK.rgba,
        'data': serialized_data
    }


def tenement_permit_category_tree(queryset, permit_type, permit_status, colour: Colour, visible=False, **kwargs):
    current_date = date.today()

    tenement_queryset = queryset.filter(
        Q(permit_type=permit_type, permit_status=permit_status)
        # & (Q(date_expiry__gt=current_date) | Q(date_expiry=None))
    )
    queryset_count = tenement_queryset.count()

    status_display = get_meta_choices_map(Tenement, 'permit_status').get(permit_status)

    return {
        'display': f'{status_display} ({queryset_count})',
        'value': f'{permit_status}',
        'colour': colour.rgba,
        'enabled': visible,
        'data': tenement_serializer(tenement_queryset)
    }


def permit_type_status_date_tree(queryset, **kwargs):
    """Generates a segmented date tree for a tenement queryset.
    The tree is in tiers of permit type, permit status and then date segments.
    """
    # These options should be changed to fit the requirements as they are changed
    tree_options = {
        'EPM':
            {
                'G': {'field': 'date_granted', 'cmap': ColourMap.GREEN.cmap},
                'A': {'field': 'date_lodged',
                      'cmap': ColourMap.create_colormap('#4556C3', '#7B9FF9', '#A37D6A', '#EE8468', '#B81131')},
                'N': {'field': 'date_expiry', 'cmap': ColourMap.PINK.cmap}
            },
        'MDL':
            {
                'G': {'field': 'date_granted', 'cmap': ColourMap.PURPLE.cmap},
                'A': {'field': 'date_lodged', 'cmap': ColourMap.TEAL.cmap},
                'N': {'field': 'date_expiry', 'cmap': ColourMap.MAROON.rcmap}
            },
        'ML':
            {
                'G': {'field': 'date_granted', 'cmap': ColourMap.ORANGE.cmap},
                'A': {'field': 'date_lodged', 'cmap': ColourMap.OLIVE.cmap},
                'N': {'field': 'date_expiry', 'cmap': ColourMap.SLATEBLUE.cmap}
            },
        'default':
            {
                'G': {'field': 'date_granted', 'cmap': ColourMap.get_cmap('summer').reversed()},
                'A': {'field': 'date_lodged', 'cmap': ColourMap.get_cmap('jet')},
                'N': {'field': 'date_expiry', 'cmap': ColourMap.get_cmap('copper')}
            },
    }

    # Initial setup
    tree = []
    permit_types, permit_type_choice_map = get_permit_type_choices(queryset)
    permit_statuses, permit_status_choice_map = get_permit_status_choices(queryset)

    # Begin graph looping
    for permit_type in permit_types:
        permit_type_options = tree_options.get(permit_type, tree_options.get('default'))
        type_branch = {
            'field': 'permit_type',
            'display': permit_type_choice_map.get(permit_type) + f' ({permit_type})',
            'value': permit_type,
            'children': []
        }

        for permit_status in permit_statuses:
            permit_queryset = queryset.filter(permit_type=permit_type, permit_status=permit_status)
            permit_status_options = permit_type_options.get(permit_status, {})

            if not permit_queryset.exists():
                continue

            date_field = permit_status_options.get('field')
            colour_map = permit_status_options.get('cmap')
            status_branch = {
                'field': 'permit_status',
                'display': permit_status_choice_map.get(permit_status) + f' ({len(permit_queryset)})',
                'value': permit_status,
                'children':
                    generate_date_range_geojson(
                        permit_queryset,
                        date_field,
                        colour_map,
                        segments=5,
                        days_per_segment=365,
                        serializer=tenement_serializer
                    )
            }

            type_branch['children'].append(status_branch)

        tree.append(type_branch)


    return tree

def map_box_tree(tenement_queryset):
    return [
        {
            'display': 'Tenements',
            'value': 'tenement',
            'children': [
                {
                    'display': 'Exploration Permit for Minerals (EPM)',
                    'value': 'epm',
                    'children': [
                        tenement_permit_category_tree(tenement_queryset, 'EPM', 'G', Colour.GREEN, True),
                        tenement_permit_category_tree(tenement_queryset, 'EPM', 'A', Colour.RED, True),
                        tenement_permit_category_tree(tenement_queryset, 'EPM', 'N', Colour.PINK, True),
                    ]
                },
                {
                    'display': 'Mining Development License (MDL)',
                    'value': 'mdl',
                    'children': [
                        tenement_permit_category_tree(tenement_queryset, 'MDL', 'G', Colour.MAGENTA, True),
                        tenement_permit_category_tree(tenement_queryset, 'MDL', 'A', Colour.BLACK, True),
                    ]
                },
                {
                    'display': 'Mining Lease (ML)',
                    'value': 'ml',
                    'children': [
                        tenement_permit_category_tree(tenement_queryset, 'ML', 'G', Colour.ORANGE, True),
                        tenement_permit_category_tree(tenement_queryset, 'ML', 'A', Colour.BROWN, True),
                    ]
                },
                {
                    'display': 'Exploration Permit for Coal (EPC)',
                    'value': 'epc',
                    'children': [
                        tenement_permit_category_tree(tenement_queryset, 'EPC', 'G', Colour.TEAL, True),
                        tenement_permit_category_tree(tenement_queryset, 'EPC', 'A', Colour.MAROON, True),
                    ]
                },
                tenement_moratorium(tenement_queryset)
            ]
        }
    ]