from http import HTTPStatus

from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry

from interactive_map.utils.core import map_api_endpoint
from interactive_map.utils.tenement import map_box_tree
from main.utils.geojson import GeoJSONSerializer
from project.utils.decorators import has_project_permission
from tms.models import Tenement, Target


@map_api_endpoint()
def tenement_endpoint(request, permit_state, permit_type, permit_number, bounding_box, *args, **kwargs):
    """api/project/<str:slug>/tenements/"""
    # Get the correct tree function, this determines how the tree is displayed, whether in date or status form
    queryset = Tenement.objects.filter(permit_state=permit_state, permit_type=permit_type, permit_number=permit_number)
    tree = map_box_tree(queryset)

    return JsonResponse(tree, safe=False, status=HTTPStatus.OK)

@map_api_endpoint()
def tenement_prospects_endpoint(request, permit_state, permit_type, permit_number, bounding_box, *args, **kwargs):
    tenement = Tenement.objects.filter(permit_state=permit_state, permit_type=permit_type, permit_number=permit_number).first()
    
    queryset = Target.objects.filter(project_id=tenement.project_id)

    # As the targets aren't having their geometry saved in the geometry field, we have to convert them
    # here.
    for target in queryset:
        if not target.area:
            lon, lat = map(float, target.location.split())

            target.area = GEOSGeometry(f"POINT({lat} {lon})")
            target.save()
            
    queryset = queryset.filter(area__intersects=tenement.area_polygons)

    tree = [
        {
            'display': 'Prospects',
            'enabled': True,
            'data': GeoJSONSerializer().serialize(queryset, geometry_field="area", fields=["name"]),
            'value': 0,
        }
    ]

    return JsonResponse(tree, safe=False, status=HTTPStatus.OK)
