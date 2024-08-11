from http import HTTPStatus
import json
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch, Count
from django.http import HttpResponseNotFound, JsonResponse, QueryDict
from django.shortcuts import render, redirect
from django.utils.formats import localize
from project.utils.post import create_project
from main.utils.query_analyze import django_query_analyze
from media_file.forms import CreateMultipleMediaFileForm
from media_file.models import MediaFile
from project.forms import CreateTargetForm, CreateTaskForm, InviteUserForm, CreateProjectForm, RegionForm
from project.models import Project, Permission,ProjectMember
from project.utils.decorators import has_project_permission
from tms.forms import AddTenementForm
from tms.models import Tenement, TenementTask
from django.contrib import messages
from django.contrib.gis.geos import GEOSGeometry
from django.core.serializers import serialize
from .forms import RegionForm
from .model_choices import CountryChoices, StateChoices

User = get_user_model()

@login_required
def new_project(request):
    region_form = RegionForm()
    form = CreateProjectForm(initial={'country': CountryChoices.Australia})
    if request.method == 'POST':
        if 'region_form_submit' in request.POST:
            region_form = RegionForm(request.POST)
            if 'country' in request.POST:
                
                country = request.POST['country']
                state_choices = StateChoices.CHOICES.get(country, [])
                region_form.fields['state'].choices = [(code, name) for code, name in state_choices]

        elif 'project_form_submit' in request.POST:
            country_Code = request.POST.get('hiddenCodeCountry')
            state_Code = request.POST.get('hiddenCodeState')    
            mutable_post = QueryDict(request.body.decode('utf-8')).copy()
            mutable_post['country'] = country_Code
            mutable_post['state'] = state_Code
            form = CreateProjectForm(mutable_post)
            if form.is_valid():
                # process the form data
                project = form.save(commit=False)
                project.owner = request.user
                project.save()
                print("pr",project.id)
                ProjectMember.objects.create(project=project, user=request.user, permission=Permission.OWNER)
                messages.success(request,"Project Created Successfully")
                return redirect('project:index')
                #messages.success(request, 'Project Created Successfully')
            else:
                #messages.error(request, form.errors)
                print("error", form.errors)
                #return redirect("project:new_project")
                #return JsonResponse({"message" : form.errors}, status=HTTPStatus.BAD_REQUEST)
    
  
    else:
            form = CreateProjectForm()
    return render(request, 'project/new_project.html', {'region_form': region_form, 'form': form})


def get_states(request):
    country_name = request.POST.get('country_name')
    states = StateChoices.CHOICES.get(country_name, [])
    state_list = [{'code': code, 'name': name} for code, name in states]
    return JsonResponse({'states': state_list})


@login_required
def project_index(request):
    return render(request, 'project/project_index.html', {
        'inviteUserForm': InviteUserForm(),
        'addTenementForm': AddTenementForm(request.user),
    })
    # return render(request, "pwc/project_index.html", {
    #     "createProjectForm": CreateProjectForm(),
    #     "deleteProjectForm": DeleteProjectForm(),
    #     "addTenementForm": AddTenementForm(instance=request.user),
    #     "deleteTenementForm": DeleteTenementForm(),
    #     "leaveProjectForm": DeleteMemberForm(instance=request.user),
    #     'deleteReportForm': UUIDForm(js=('/static/pwc/js/delete_report_form.js',)),
    # })


@login_required
def my_projects(request):
    return render(request, 'my_projects/my_projects.html', {
        'inviteUserForm': InviteUserForm(),
        'addTenementForm': AddTenementForm(request.user),
    })

@login_required
def my_tenements(request):
    return render(request, 'my_tenements/my_tenements.html', {
        'inviteUserForm': InviteUserForm(),
        'addTenementForm': AddTenementForm(request.user),
    })

@login_required
def project_kms_view(request):
    return render(request, 'kms_view/kms_view.html')

@login_required
def project_lms_view(request):
    return render(request, 'lms_view/lms_view.html')


@has_project_permission(Permission.READ, allow_sudo=True)
def project_file_download(request, project, slug, uuid):
    try:
        media_file: MediaFile = project.files.get(id=uuid)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    return media_file.to_file_response()


@has_project_permission(Permission.READ)
def project_dashboard(request, project, slug):

    # The requesting member object
    member = project.request_member[0]

    context = {
        'project': project,
        'member': member,
        'messageUserForm': None,  # MessageUserForm(user_assumed=True),
        'deleteTenementForm': None,  # DeleteTenementForm()
    }

    if member.is_write():
        context = {**context, **{
            'createTaskForm': CreateTaskForm(instance=project),
            'createDatasetForm': CreateMultipleMediaFileForm(allowed_extensions=MediaFile.Extensions.EXCEL + MediaFile.Extensions.DATA),
            'createModelForm': CreateMultipleMediaFileForm(allowed_extensions=MediaFile.Extensions.MODELS),
        }}

    if member.is_admin():
        context = {**context, **{
            'addTenementForm': AddTenementForm(request.user, project=project.slug),
            'createTargetForm': CreateTargetForm(instance=project, user=request.user),
            'inviteUserForm': InviteUserForm(inviter=request.user, project=project),
        }}
        

    return render(request, "project/project_dashboard.html", context)


@login_required
def get_projects(request):
    return JsonResponse(
        Project.objects.to_datatable(request, members__user=request.user),
        status=HTTPStatus.OK
    )

@login_required
def get_tenements(request):
    """Retrieves ALL of a users Tenements in JSON format."""
    return JsonResponse(
        Tenement.objects.to_datatable(request, project__members__user=request.user),
        status=HTTPStatus.OK
    )

@has_project_permission()
def get_project_tenements(request, project: Project, slug):
    """Retrieves the Tenements in JSON format from a Project's Dashboard. """
    return JsonResponse(
        Tenement.objects.to_datatable(request, project=project),
        status=HTTPStatus.OK
    )

@has_project_permission()
def get_project_map(request, project: Project, slug):
    return render(request, "project/project_map.html",
                  {'slug': slug,}, content_type='application/json')


@has_project_permission()
def get_targets(request, project: Project, slug):
    
    target_data= []
    
    targets = project.targets.all()
    
    for target in targets:
        lon, lat = map(float, target.location.split())
        target_area = GEOSGeometry(f"POINT({lat} {lon})")
        
        overlapping_tenements = project.tenements.filter(
            area_polygons__intersects=target_area
            )
        
        target_permits = [{
                'type': tenement.permit_type,
                'number': tenement.permit_number,
                'slug': tenement.get_absolute_url(),
        } for tenement in overlapping_tenements]
        
        target_data.append({
            'permit': target_permits,
            'name': target.name,
            'description': target.description,
            'location': target.location,
            'actions': None,
        })

    return JsonResponse({'data': target_data,}, status=HTTPStatus.OK)


@has_project_permission()
def get_members(request, project: Project, slug):
    members = project.members.select_related('user').all()

    # Get some information about the current user
    request_member = project.request_member[0]

    context = []

    for member in members:
        # Set up actions, essentially what a user can do to other users in the table
        actions = []

        if member.user != request.user:
            actions.append('message')

        # If the requesting member is an admin, and they have permissions greater than the looped member
        if member.is_admin() and member.permission < request_member.permission:
            actions.append('remove')
            actions.append('modify')

        # Add table row context
        context.append({
            'name': member.user.full_name,
            'email': member.user.email,
            'permission': member.get_permission_display(),
            'join_date': localize(member.join_date),  # .strftime('%b. %d, %Y'),
            'actions': actions,
        })

    return JsonResponse({'data': context}, status=HTTPStatus.OK)


@has_project_permission()
def get_datasets(request, project: Project, slug):
    media_files = project.files.filter(tag=MediaFile.DATASET).prefetch_related(
        Prefetch('children', queryset=project.files.filter(tag=MediaFile.CLEANER), to_attr='cleaned_files')
    ).all()

    context = {'data': [{
        'uuid': str(media.id),
        'file': {
            'url': project.get_file_url(media.id),
            'filename': media.filename,
        },
        'size': media.file_size_str,
        'dateCreated': media.date_created,
        'actions': None,
        # 'cleaned': [{
        #     'url': reverse('project:get_file', kwargs={'slug': project.slug, 'uuid': str(cleaned.id)}),
        #     'filename': cleaned.filename,
        # } for cleaned in dataset.cleaned_files]
    } for media in media_files]}

    return JsonResponse(context, status=HTTPStatus.OK)


@has_project_permission()
def get_models(request, project: Project, slug):
    media_files = project.files.filter(tag=MediaFile.MODEL).all()

    context = {'data': [{
        'uuid': str(media.id),
        'file': {
            'url': project.get_file_url(media.id),
            'filename': media.filename,
        },
        'size': media.file_size_str,
        'dateCreated': media.date_created,
        'actions': None,
    } for media in media_files]}

    return JsonResponse(context, status=HTTPStatus.OK)


@has_project_permission()
def get_reports(request, project: Project, slug):
    media_files = project.files.filter(tag=MediaFile.REPORT).all()

    context = {'data': [{
        'uuid': str(media.id),
        'file': {
            'url': project.get_file_url(media.id),
            'filename': media.filename,
        },
        'size': media.file_size_str,
        'dateCreated': media.date_created,
        'actions': None,
    } for media in media_files]}

    return JsonResponse(context, status=HTTPStatus.OK)


@has_project_permission()
def get_tasks(request, project: Project, slug):
    tasks = TenementTask.objects.filter(tenement__project=project).prefetch_related('files').all()
    context = {
        'data': [task.as_table_row() for task in tasks]
    }

    return JsonResponse(context, status=HTTPStatus.OK)
