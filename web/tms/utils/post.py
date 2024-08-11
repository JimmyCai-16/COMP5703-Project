from http import HTTPStatus

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.serializers import serialize
from django.contrib.gis.geos import GEOSGeometry

from notification.utils.utils import notify_project_members
from project.forms import CreateTaskForm
from project.models import Permission
from project.utils.decorators import has_project_permission
from tms.forms import ClaimTenementForm, CreateWorkProgramForm, WorkProgramReceiptForm
from tms.models import Tenement, WorkProgram
from main.utils.fields import ChoicesLabelCase
from django.contrib import messages

import interactive_map.views.main as im_views
from project.forms import CreateTargetForm
from tms.models import Target
from project.models import Project

"""Various functions to handle certain post requests. Most of these are used across various pages.

Error messages that are shown for invalid input are generally formatted in the way the django forms 
would perform. However, the error handling for catching invalid requests based on things like 
people who fake requests or modify javascript to allow certain requests don't return any valuable 
information.
"""


@require_POST
def claim_tenement(request, permit_state, permit_type, permit_number):
    """Claims a tenement for the incoming project"""
    tenement = Tenement.objects.get(permit_state=permit_state, permit_type=permit_type, permit_number=permit_number)
    form = ClaimTenementForm(user=request.user, tenement=tenement, data=request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, 'Tenement Claimed Successfully')

        # Notify members of the project
        notify_project_members(
            project=tenement.project,
            user_from=request.user,
            summary=f"The Tenement <b>{tenement}</b> claimed into <b>{tenement.project}</b> by <b>{request.user}</b>.",
            url=tenement.get_absolute_url()
        )

        return JsonResponse({}, status=HTTPStatus.OK)
    else:
        return JsonResponse(form.errors, status=HTTPStatus.BAD_REQUEST)


@require_POST
@has_project_permission(Permission.ADMIN)
def relinquish_tenement(request, tenement, permit_state, permit_type, permit_number):
    """Relinquishes a tenement from its project"""
    print("tenement to delete", tenement)

    # Notify members of the project
    notify_project_members(
        project=tenement.project,
        user_from=request.user,
        summary=f"The Tenement <b>{tenement}</b> was relinquished from <b>{tenement.project}</b> by <b>{request.user}</b>.",
        url=tenement.get_absolute_url()
    )

    # Relinquish now that we have created the message
    tenement.project = None
    tenement.save()
    messages.success(request, 'Tenement relinquished Successfully')

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def delete_task(request, tenement, permit_state, permit_type, permit_number):
    """Deletes a task from the tenement"""
    try:
        task_id = request.POST.get('task')
        task = tenement.tasks.get(id=task_id)

        # Notify members of the project
        notify_project_members(
            project=tenement.project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> deleted the task <b>{task}</b> from <b>{tenement}</b>.",
            url=tenement.get_absolute_url()
        )

        task.delete()
        messages.success(request, 'Task Deleted Successfully')

    except ObjectDoesNotExist:
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def archive_task(request, tenement, permit_state, permit_type, permit_number):
    # TODO: Archive Task, is it necessary?
    print(tenement, request.POST)
    return JsonResponse({}, status=HTTPStatus.NOT_IMPLEMENTED)


@require_POST
@has_project_permission(Permission.ADMIN)
def modify_task(request, tenement, permit_state, permit_type, permit_number):
    # TODO: Modify Task POST
    print(tenement, request.POST)
    return JsonResponse({}, status=HTTPStatus.NOT_IMPLEMENTED)


@require_POST
@has_project_permission(Permission.WRITE)
def add_target(request, tenement, permit_state, permit_type, permit_number):
    tenement = Tenement.objects.get(permit_state=permit_state, permit_type=permit_type, permit_number=permit_number)
    tenement_geojson = serialize("geojson", [tenement], geometry_field="area_polygons", fields=["permit_type", "permit_number"])
    post_data = request.POST.copy()
    try:
        project = Project.objects.prefetch_related('targets').get(tenements__id=tenement.id, members__user=request.user)

    except Exception:
        print('error adding target')
        
    post_data['project'] = project.id
    lon, lat = map(float, post_data.get('location').split())
    post_data['area'] = GEOSGeometry(f"POINT({lat} {lon})")
    target_form = CreateTargetForm(user=request.user, data=post_data or None)
    if target_form.is_valid():
        target = target_form.save()

        context = {
            'data': {
                'name': target.name,
                'description': target.description,
                'location': target.location,
                'actions': None,
            },
            'tenement': tenement_geojson,
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
        err = ""
        for field, errors in target_form.errors.items():
            for error in errors:
               err += error
        return JsonResponse(target_form.errors, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(context, status=HTTPStatus.OK)

@require_POST
@has_project_permission(Permission.WRITE)
def edit_target(request, tenement, permit_state, permit_type, permit_number, target_name):
    tenement = Tenement.objects.get(permit_state=permit_state, permit_type=permit_type, permit_number=permit_number)
    tenement_geojson = serialize("geojson", [tenement], geometry_field="area_polygons", fields=["permit_type", "permit_number", "permit_status", "date_lodged", "date_granted", "ahr_name"])
    
    try:
        project = Project.objects.prefetch_related('targets').get(tenements__id=tenement.id, members__user=request.user)

    except Exception:
        print('error editing target')
    target = Target.objects.get(project=project, name=target_name)
    post_data = request.POST.copy()
    
    target.name = post_data.get('name')
    target.location = post_data.get('location')
    target.description = post_data.get('description')
    lon, lat = map(float, target.location.split())
    target.area = GEOSGeometry(f"POINT({lat} {lon})")
    
    target.save()
    print('target save')
    messages.success(request, 'Target Updated Successfully')
 
    # Return the updated target data as JSON
    context = {
            'data': {
                'name': target.name,
                'description': target.description,
                'location': target.location,
                'actions': None,
            },
            'tenement': tenement_geojson,
        }
    return JsonResponse(context, status=HTTPStatus.OK)



@require_POST
@has_project_permission(Permission.ADMIN)
def delete_target(request, tenement, permit_state, permit_type, permit_number):
    try:
        target_name = request.POST.get('name')
        try:
            project = Project.objects.prefetch_related('targets').get(tenements__id=tenement.id, members__user=request.user)

        except Exception:
            print('error deleting target')
        target = Target.objects.get(project=project, name=target_name)
        target.delete()
        messages.success(request, 'Target Deleted Successfully')

        # Notify members of the project
        notify_project_members(
            project=project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> deleted target <b>{target}</b> from <b>{project}</b>.",
            url=reverse('project:dashboard', kwargs={'slug': project.slug})
        )

    except ObjectDoesNotExist as e:
        print(e)
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.WRITE)
def add_task(request, tenement, permit_state, permit_type, permit_number):
    post_data = request.POST.copy()
    post_data['tenement'] = tenement.id

    task_form = CreateTaskForm(data=post_data or None, files=request.FILES or None, instance=tenement)

    if task_form.is_valid():
        task = task_form.save()

        context = {
            'data': task.as_table_row()
        }
        messages.success(request, 'Task Added Successfully')

        # Notify members of the project
        notify_project_members(
            project=tenement.project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> created the task <b>{task}</b> from <b>{tenement}</b>.",
            url=tenement.get_absolute_url()
        )

        # return JsonResponse(context, status=HTTPStatus.OK)
    else:
        err = ""
        for field, errors in task_form.errors.items():
            for error in errors:
                
                err += error
        return JsonResponse(task_form.errors, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse(context, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.WRITE)
def add_workload(request, tenement, permit_state, permit_type, permit_number):
    """Adds a workload object to the tenement"""
    work_program_form = CreateWorkProgramForm(data=request.POST or None, instance=tenement)

    if work_program_form.is_valid():
        program = work_program_form.save()

        context = {
            'data': {
                'year': program.year,
                'expenditure': program.estimated_expenditure,
                'discipline': program.discipline,
                'activity': program.activity,
                'units': program.units,
                'quantity': program.quantity,
            }
        }

        # Notify members of the project
        notify_project_members(
            project=tenement.project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> added workload <b>{program}</b> to <b>{tenement}</b>.",
            url=tenement.get_absolute_url()
        )

        messages.success(request, 'WorkLoad Added Successfully')
    else:
        err = ""
        for field, errors in work_program_form.errors.items():
            for error in errors:
                err += error
        return JsonResponse(work_program_form.errors, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse(context, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def delete_workload(request, tenement, permit_state, permit_type, permit_number):
    # TODO: Work Program
    try:
        program_id = request.POST.get('program')
        program = tenement.work_programs.get(id=program_id)

        # Notify members of the project
        notify_project_members(
            project=tenement.project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> deleted workload <b>{program}</b> from <b>{tenement}</b>.",
            url=tenement.get_absolute_url()
        )

        # Delete the program
        program.delete()
        messages.success(request, 'WorkLoad Deleted Successfully')

    except ObjectDoesNotExist:
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    return JsonResponse({}, status=HTTPStatus.OK)


@require_POST
@has_project_permission(Permission.ADMIN)
def modify_workload(request, tenement, permit_state, permit_type, permit_number):
    # TODO: Work Program
    print(tenement, request.POST)
    return JsonResponse({}, status=HTTPStatus.NOT_IMPLEMENTED)


@require_POST
@has_project_permission(Permission.WRITE)
def add_workload_receipt(request, tenement, permit_state, permit_type, permit_number, work_program):
    """Adds a receipt to a work program"""
    try:
        work_program = tenement.work_programs.get(id=work_program)
    except ObjectDoesNotExist:
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    form = WorkProgramReceiptForm(work_program=work_program, data=request.POST or None, files=request.FILES or None)

    if form.is_valid():
        receipt = form.save()
        messages.success(request, 'Receipt Added Successfully')

        # Notify members of the project
        notify_project_members(
            project=tenement.project,
            user_from=request.user,
            summary=f"<b>{request.user}</b> added receipt to <b>{work_program}</b> in <b>{tenement}</b>.",
            url=tenement.get_absolute_url()
        )

        context = {
            # TODO: Do we need to send anything back to the client?
        }
        return JsonResponse(context, status=HTTPStatus.OK)

    return JsonResponse(form.errors, status=HTTPStatus.BAD_REQUEST)
