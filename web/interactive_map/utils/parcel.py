from django.contrib.gis.geos import GEOSGeometry
from django.http import JsonResponse
from django.utils.text import slugify

from interactive_map.utils.core import get_field_unique_values, get_meta_choices_map, ColourMap, Colour
from lms.models import Parcel
from main.utils.geojson import GeoJSONSerializer
from project.utils.decorators import has_project_permission


def get_parcel_type_choices(queryset):
    """Returns a tuple of all possible options for a queryset, and all possible options for a model."""
    return list(get_field_unique_values(queryset, 'parcel_type'))


def project_parcel_type_tree(queryset):
    # # Step 1: Identify objects with shared values
    # shared_values_queryset = Parcel.objects.values('lot', 'plan').annotate(count=Count('id')).filter(
    #     count__gt=1)
    #
    # print('shared_values_queryset', len(shared_values_queryset))
    #
    # # Step 2: Group objects based on shared values
    # for shared_values in shared_values_queryset:
    #     group_queryset = Parcel.objects.filter(pk__in=group_queryset).annotate(unioned_geometry=Func('geometry', function='ST_Union')).values('unioned_geometry')[0]['unioned_geometry']
    #
    # # Step 4: Update the geometry field using raw SQL query
    # update_sql = f"UPDATE yourapp_yourmodel SET geometry = ST_Union(geometry, ST_GeomFromGeoJSON(%s)) WHERE id = %s"
    # with connection.cursor() as cursor:
    #     cursor.execute(update_sql, [unioned_geometry.geojson, group_queryset.first().id])
    #
    # # Step 5: Delete the original objects in a single query
    # group_queryset.exclude(pk=group_queryset.first().pk).delete()

    # Initial setup
    tree = []
    parcel_types = list(get_field_unique_values(queryset, 'parcel__parcel_type'))

    for parcel_type in parcel_types:
        parcel_type_queryset = queryset.filter(parcel__parcel_type=parcel_type).all()
        value = slugify(parcel_type)
        for obj in parcel_type_queryset:
            obj.parcelid = obj.parcel.id
            #delattr(obj, 'parcel__id')
        type_branch = {
            'field': 'parcel_type',
            'display': parcel_type,
            'value': value,
            'enabled': True,
            'colour': Colour.from_string_hash(parcel_type),
            'data': GeoJSONSerializer().serialize(
                parcel_type_queryset,
                geometry_field="parcel__geometry",
                fields=[
                    'id',
                    'parcelid',
                    'parcel__lot',
                    'parcel__plan',
                    'parcel__tenure',
                    'parcel__feature_name',
                    'parcel__alias_name',
                    'parcel__accuracy_code',
                    'parcel__surv_index',
                    'parcel__cover_type',
                    'parcel__parcel_type',
                    'parcel__locality',
                    'parcel__shire_name',
                    'parcel__smis_map',
                    'owner_count',
                    'active'
                ],
                
            )
        }

        tree.append(type_branch)

    return tree

    #
    # features = []
    # for parcel in queryset:
    #     # Layer is supposed to be categorised by parcel owner, which I assume would be the owner who's date of ownership
    #     # was most recent?
    #     owner = parcel.projectparcel_set.get(project=project).owners.order_by(
    #         '-parcel_relationships__date_ownership_start').first()
    #
    #     features.append({
    #         'type': 'Feature',
    #         'geometry': json.loads(str(GEOSGeometry(parcel.geometry).geojson)),
    #         'properties': {
    #             'lot': parcel.lot,
    #             'plan': parcel.plan,
    #             'tenure': parcel.tenure,
    #             'owner': owner.__str__() if owner else 'Unowned',
    #             'shire_name': parcel.shire_name,
    #             'feature_name': parcel.feature_name,
    #             'alias_name': parcel.alias_name,
    #             'locality': parcel.locality,
    #             'parcel_type': parcel.parcel_type,
    #             'cover_type': parcel.cover_type,
    #             'accuracy_code': parcel.accuracy_code,
    #             'smis_map': parcel.smis_map,
    #         }
    #     })
    #
    # feature_collection = {
    #     "type": "FeatureCollection",
    #     "crs": {
    #         "type": "name",
    #         "properties": {
    #             "name": "EPSG:4326"  # Example CRS identifier (WGS 84)
    #         }
    #     },
    #     "features": features
    # }
    #
    # geojson = json.dumps(feature_collection, indent=2)
    #
    # return JsonResponse(geojson, safe=False, status=200)  # GeoJSONSerializer(data, "geometry", fields).as_response()
