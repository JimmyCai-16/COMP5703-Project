from http import HTTPStatus

from django.http import JsonResponse
from django.shortcuts import reverse
from django.views.decorators.http import require_POST
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q

from notification.utils.utils import notify_project_members
from project.models import Permission
from project.forms import CreateTargetForm
from project.utils.decorators import has_project_permission
from django.contrib import messages


@require_POST
@has_project_permission(Permission.WRITE)
def add_target(request, project, slug):
    post_data = request.POST.copy()
    post_data['project'] = project.id
    lon, lat = map(float, post_data.get('location').split())
    target_area = GEOSGeometry(f"POINT({lat} {lon})")
    post_data['area'] = target_area 

    target_form = CreateTargetForm(user=request.user, data=post_data or None)
    if target_form.is_valid():
        target = target_form.save()
        
        overlapping_tenements = project.tenements.filter(
            Q(area_polygons__intersects = target_area )
            )
        if overlapping_tenements.exists():
            target_permits = [{
                    'type': tenement.permit_type,
                    'number': tenement.permit_number,
                    'slug': tenement.get_absolute_url(),
            } for tenement in overlapping_tenements]
        else:
            target_permits = []

        context = {
            'data': {
                'permit': target_permits,
                'name': target.name,
                'description': target.description,
                'location': target.location,
                'actions': None,
            },
        }
        messages.success(request, 'Target Created Successfully')
        # return JsonResponse(context, status=HTTPStatus.OK)

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> created a new target in <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )
    else:
        print('error happened')
        err = ""
        for field, errors in target_form.errors.items():
            for error in errors:
               err += error
        return JsonResponse(target_form.errors, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(context, status=HTTPStatus.OK)