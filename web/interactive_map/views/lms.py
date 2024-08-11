from http import HTTPStatus

from django.db.models import Count
from django.http import JsonResponse

from interactive_map.utils.parcel import project_parcel_type_tree
from lms.models import ProjectParcel
from project.models import Project


def lms_parcels_endpoint(request, slug, parcel=None, *args, **kwargs):
    # Get the project as we need its geometry
    project = Project.objects.get(slug=slug)

    # Create project parcels where needed for the project
    ProjectParcel.objects.bulk_create_for_project(project=project)

    # Get the projects parcels and annotate the owner count
    queryset = ProjectParcel.objects.filter(project=project).annotate(owner_count=Count('owners'))

    # Generate the leaflet tree
    tree = [
        {
            'display': 'Parcels',
            'value': 'project_parcel',
            'children': project_parcel_type_tree(queryset)
        }
    ]

    return JsonResponse(tree, safe=False, status=HTTPStatus.OK)
