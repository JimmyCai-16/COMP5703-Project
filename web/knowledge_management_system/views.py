import io
import json
from http import HTTPStatus
import os

import django.core.exceptions
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import resolve
from django.views import View

from project.forms import CreateTaskForm
from project.models import Permission
from project.utils.decorators import has_project_permission
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, HttpResponseServerError, \
    HttpResponseBadRequest
from django.core import exceptions
from django.shortcuts import render, redirect
from django.db import models

from project.forms import CreateTargetForm

from tms.models import Target
from project.models import Project, ProjectMember
from knowledge_management_system.forms import *
from knowledge_management_system.models import *
from knowledge_management_system.utils.report import WorkReportPDF, StatusReportPDF, HistoricalReportPDF
from media_file.models import MediaFile

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from bs4 import BeautifulSoup
import base64
from django.http import QueryDict

from tms.models import Target, TenementTask


@has_project_permission()
def project_page(request, project, **kwargs):
    try:
        kms = KMSProject.objects.get(project=project)
    except KMSProject.DoesNotExist:
        kms = KMSProject.objects.create(project=project)
    context = {
        'project': project,
        'member': project.request_member[0],
        'kms': kms,
        'prospects': [{'id': str(prospect.id), 'name': prospect.name} for prospect in project.targets.all()]
    }

    return render(request, 'knowledge_management_system/project_page.html', context)


# def debug_permission_setup(view, request, *args, **kwargs):
#     # Delete all the users permissions for the memes
#     ObjectPermission.objects.filter(content_object=view.kms_project, user=request.user).delete()
#
#     if view.member.is_admin():
#         permissions = [
#             ObjectPermission(content_object=view.kms_project, user=request.user, permission=perm)
#             for perm in [
#                 'modify',
#                 'delete',
#                 'add_report',
#                 'delete_report',
#                 'modify_report',
#             ]
#         ]
#
#         ObjectPermission.objects.bulk_create(permissions)
#
#     view.permissions = ObjectPermission.objects.filter(content_object=view.kms_project, user=request.user)


class KMSView(LoginRequiredMixin, View):
    template_name = ''
    url_name = ''
    group_name = ''
    get_permission = Permission.READ
    post_permission = Permission.ADMIN
    delete_permission = Permission.ADMIN

    member = None
    project = None
    kms_project = None
    instance = None
    permissions = []

    @classmethod
    def as_view(cls, **kwargs):
        cls.get_permission = kwargs.get('get_permission', cls.get_permission)
        cls.post_permission = kwargs.get('post_permission', cls.post_permission)
        cls.delete_permission = kwargs.get('delete_permission', cls.delete_permission)

        return super().as_view(**kwargs)

    def get_group_name(self):
        """Group name for the Django Channel (websocket related)"""
        return None

    def pre_dispatch(self, request, *args, **kwargs):
        """Performs some additional setup before the HTTP method is dispatched. Typically used for initialising the
                views queryset or instance objects."""
        pass

    def dispatch(self, request, *args, **kwargs):
        """Sets up the project, and if the user exists in the project with the correct permissions, raises ObjectDoesNotExist"""
        self.url_name = resolve(self.request.path_info).url_name

        print(
            f'{request.scheme.upper()} {request.method} {self.__class__.__name__}("{self.url_name}") : {kwargs}\n\t{request.POST if request.POST else request.GET}')

        # Identify correct permission for method
        if request.method == 'GET' and self.get_permission:
            permission = self.get_permission
        elif request.method == 'POST' and self.post_permission:
            permission = self.post_permission
        elif request.method == 'DELETE' and self.delete_permission:
            permission = self.delete_permission
        else:
            return JsonResponse({}, status=HTTPStatus.METHOD_NOT_ALLOWED)

        # Retrieve the Project and Member
        try:
            slug = kwargs.get('slug')
            self.member = ProjectMember.objects.select_related('project').get(
                project__slug=slug, user=self.request.user, permission__gte=permission
            )
            self.project = self.member.project
        except (Project.DoesNotExist, ProjectMember.DoesNotExist):
            return redirect('project:index')

        # Get the KMS project
        try:
            self.kms_project, _ = KMSProject.objects.get_or_create(project=self.project)
        except KMSProject.MultipleObjectsReturned:
            self.kms_project = KMSProject.objects.filter(project=self.project).first()
        except django.db.IntegrityError:
            return redirect('kms:project_page', slug=slug)

        # Perform pre dispatch logic
        try:
            self.pre_dispatch(request, *args, **kwargs)
        except Exception as e:
            return HttpResponseBadRequest(e)

        # Setup Permissions
        # debug_permission_setup(self, request, args, kwargs)

        # Finally dispatch to correct method
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return JsonResponse({}, status=HTTPStatus.METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        return JsonResponse({}, status=HTTPStatus.METHOD_NOT_ALLOWED)

    def delete(self, request, *args, **kwargs):
        return JsonResponse({}, status=HTTPStatus.METHOD_NOT_ALLOWED)


class ProjectView(KMSView):
    template_name = 'knowledge_management_system/project_page.html'
    prospects = None
    permissions = []

    def get_group_name(self):
        return f"kms-project-page-{self.project.slug}"

    def pre_dispatch(self, request, *args, **kwargs):
        self.instance = self.kms_project  # Our instance for this view is the kms_project so set it as such

    def get(self, request, *args, **kwargs):
        prospects = [{'id': str(prospect.id), 'name': prospect.name, } for prospect in self.project.targets.all()]

        # current_permission = self.member.permission
        #
        # if current_permission == Permission.ADMIN:

        # Send the signal to the group
        # channel_layer = get_channel_layer()
        #
        # async_to_sync(channel_layer.group_send)(
        #     f"kms-project-page-{self.project.slug}",
        #     {
        #         'type': 'send_model_instance',
        #         'model': 'prospect',
        #         'instance': KMSProspect.objects.first().as_instance_dict(),
        #     }
        # )
        companies = []
        for i in KMSHistoricalReport.objects.filter(kms_project=self.kms_project, is_template=False):
            if i.company not in companies:
                companies.append(i.company)

        return render(request, self.template_name, {
            'project': self.project,
            'member': self.member,
            'kms': self.instance,
            'prospects': prospects,
            'createTaskForm': CreateTaskForm(instance=self.project),
            'createTargetForm': CreateTargetForm(instance=self.project, user=request.user),
            'work_report_form': KMSWorkReportForm(project=self.project),
            'status_report_form': KMSStatusReportForm(project=self.project),
            'historical_report_form': KMSHistoricalReportForm(project=self.project),
            'companies': companies,
        })

class ProjectFieldView(ProjectView):
    """Project interface between view and channel for performing model updates and distributing them (such as a tinymce
    textarea being saved)"""
    get_permission = None
    post_permission = Permission.WRITE

    def get(self, request, *args, **kwargs):
        return HttpResponse('', status=HTTPStatus.METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        element = request.POST['id']
        content = request.POST['content']
        print(request.FILES)

        content = update_html_with_images_from_files(content, request.FILES)

        try:
            model, field_name = element.split('.')
            field = self.instance._meta.get_field(field_name)
        except (ValueError, exceptions.FieldDoesNotExist):
            return JsonResponse({}, status=HTTPStatus.NOT_ACCEPTABLE)

        # Only save if the content has changed, and it's not the ID field
        if content != getattr(self.instance, field_name) and type(field) not in (models.AutoField, models.UUIDField):
            setattr(self.instance, field_name, content)
            self.instance.save()
        else:
            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

        # Send the signal to the group
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            self.get_group_name(),
            {
                'type': 'send_field_content',
                'user': request.user,
                'element': element,
                'content': content,
            }
        )

        return JsonResponse({}, status=HTTPStatus.OK)


class ProspectView(KMSView):
    """Base view for the Prospect (or tenement Target)"""
    template_name = 'knowledge_management_system/prospect_page.html'
    target = None
    get_permission = Permission.READ
    post_permission = Permission.ADMIN
    all_reports = []

    def get_group_name(self):
        return f"kms-prospect-page-{self.project.slug}-{self.instance.prospect.id}"

    def pre_dispatch(self, request, *args, **kwargs):
        self.target_id = kwargs.get('target')

        try:
            self.instance, _ = KMSProspect.objects.select_related('prospect').get_or_create(prospect__id=self.target_id,
                                                                                            prospect__project=self.project)
            self.target = Target.objects.get(id=self.target_id)
            historical_reports = KMSHistoricalReport.objects.filter(prospect_tags=self.instance.id)
            work_reports = KMSWorkReport.objects.filter(prospect_tags=self.instance.id)
            status_reports = KMSStatusReport.objects.filter(prospect_tags=self.instance.id)
            all_reports = []
            for i in historical_reports:
                all_reports.append({"type": "Historical", "id": i.id, "name": i.name, "date_created": i.date_created,
                                    "summary": i.summary})
            for i in work_reports:
                all_reports.append(
                    {"type": "Work", "id": i.id, "name": i.name, "date_created": i.date_created, "summary": i.summary})
            for i in status_reports:
                all_reports.append({"type": "Status", "id": i.id, "name": i.name, "date_created": i.date_created,
                                    "summary": i.operational_summary})
            self.all_reports = sorted(all_reports, key=lambda x: x["date_created"], reverse=True)
        except KMSProspect.MultipleObjectsReturned:

            self.instance = KMSProspect.objects.filter(prospect_id=self.target_id).first()
        except Exception as e:
            print(e)

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name, {
            'project': self.project,
            'member': self.member,
            'kms': self.instance,
            'target': self.target,
            'all_reports': self.all_reports,
            'work_report_form': KMSWorkReportForm(project=self.project),
            'status_report_form': KMSStatusReportForm(project=self.project),
            'historical_report_form': KMSHistoricalReportForm(project=self.project)
        })


class ProspectFieldView(ProspectView, ProjectFieldView):
    """Prospect interface between view and channel for performing model updates and distributing them (such as a tinymce
    textarea being saved)"""
    get_permission = None
    post_permission = Permission.WRITE

    def get(self, request, *args, **kwargs):
        # We have to revert the get method here since the ProspectView has it initialized
        return HttpResponse('', status=HTTPStatus.METHOD_NOT_ALLOWED)


class FormView(KMSView):
    get_permission = Permission.ADMIN
    post_permission = Permission.ADMIN
    form = None
    model = None
    tag = None

    def pre_dispatch(self, request, *args, **kwargs):
        model_name = kwargs.get('model_name', None)

        # Set the model and form depending on the model_name param.
        if model_name == 'work_report' or model_name == 'work_report_form':
            self.model = KMSWorkReport
            self.form = KMSWorkReportForm
        elif model_name == 'status_report_form' or model_name == 'status_report':
            self.model = KMSStatusReport
            self.form = KMSStatusReportForm
        elif model_name == 'historical_report' or model_name == 'historical_report_form':
            self.model = KMSHistoricalReport
            self.form = KMSHistoricalReportForm
        else:
            raise Exception("Invalid Model")

    def get(self, request, *args, **kwargs):
        """Used for receiving a rendered form containing the instance variables. Primarily for importing templates or
        displaying pre-existing data."""
        instance_id = kwargs.get('id', None)
        if self.model and self.form and instance_id:
            instance = self.model.objects.get(kms_project=self.kms_project, id=instance_id)
            form = self.form(project=self.project, instance=instance)

            return JsonResponse({'html': form.render()}, status=HTTPStatus.OK)

        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        """Primarily for modifying/creating/deleting forms"""
        if not (self.model and self.form):
            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

        # Check for instance in the post data
        instance_id = request.POST.get('instance_id', None)

        if instance_id and instance_id != "-1":
            instance = self.model.objects.get(id=instance_id)
        else:
            instance = None

        modified_post_data = QueryDict(request.POST.urlencode(), mutable=True)
        for field_name in modified_post_data.keys():
            field_values = modified_post_data.getlist(field_name)
            modified_field_values = [update_html_with_images_from_files(value, request.FILES) for value in field_values]
            modified_post_data.setlist(field_name, modified_field_values)

        # Create the form
        form = self.form(modified_post_data or None, project=self.project, instance=instance)
        if form.is_valid():
            instance = form.save()
            context = instance.as_instance_dict()

            # Send the signal to the group
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"kms-project-page-{self.project.slug}",
                {
                    'type': 'send_model_instance',
                    'model': instance.model_name,
                    'instance': context,
                }
            )

            return JsonResponse(context, status=HTTPStatus.OK)
        else:
            print(form.errors)

            return JsonResponse(form.errors, status=HTTPStatus.BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Used for deleting forms."""
        instance_id = kwargs.get('id', None)

        if self.model and self.form and instance_id:
            self.model.objects.get(kms_project=self.kms_project, id=instance_id).delete()

            return JsonResponse({}, status=HTTPStatus.OK)

        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)


class SerializeDatatable(KMSView):
    """For returning a queryset as datatable content."""
    model = None
    queryset = []

    def pre_dispatch(self, request, *args, **kwargs):
        model_name = kwargs.get('model_name', None)

        # Set the model and form depending on the model_name param.
        if model_name == 'work_report':
            self.queryset = KMSWorkReport.objects.filter(kms_project=self.kms_project, is_template=False)
        elif model_name == 'status_report':
            self.queryset = KMSStatusReport.objects.filter(kms_project=self.kms_project, is_template=False)
        elif model_name == 'historical_report':
            self.queryset = KMSHistoricalReport.objects.filter(kms_project=self.kms_project, is_template=False)
            if request.GET:
                company_name = request.GET.get('companyFilter')
                if company_name:
                    self.queryset = self.queryset.filter(company=company_name)

        elif model_name == 'prospect':
            self.queryset = KMSProspect.objects.filter(prospect__project=self.project, is_template=False)
        elif model_name == 'maps':
            self.queryset = KMSProspect.objects.none()
        else:
            raise Exception("Invalid Model")

    def get(self, request, *args, **kwargs):

        if self.queryset.exists():
            # Configure pagination
            page_number = int(request.GET.get('page', 1))  # Get the current page number
            page_length = int(request.GET.get('pageLength', 10))  # No entries per page

            paginator = Paginator(self.queryset, per_page=page_length)  # Set the desired items per page
            page_obj = paginator.get_page(page_number)  # Get the Page object for the current page

            # Serialize the data from the current page
            serialized_data = [item.as_instance_dict() for item in page_obj]

            # Create the JSON response
            response_data = {
                'data': serialized_data,
                'permission': self.member.permission,
                'recordsTotal': paginator.count,
                'recordsFiltered': paginator.count,
            }

        else:
            # Create the JSON response for no records
            response_data = {
                'data': [],
                'permission': self.member.permission,
                'recordsTotal': 0,
                'recordsFiltered': 0,
            }

        return JsonResponse(response_data)


def get_tenements_json(request, project=None, slug=None, permit_state=None, permit_type=None, permit_number=None,
                       tenement=None, state=None, target=None):
    from interactive_map.views import load_json
    import os
    json_data = load_json(os.path.join('interactive_map/static/interactive_map/json/', 'tenements.json'))
    return JsonResponse(json_data)


class GetReportsView(KMSView):
    model = None
    pdf = None
    model_name = None

    def pre_dispatch(self, request, *args, **kwargs):
        # Set the model and form depending on the model_name param.
        self.model_name = kwargs.get('model_name', None)

        if self.model_name == 'work_report':
            self.model = KMSWorkReport
            self.pdf = WorkReportPDF
        elif self.model_name == 'status_report':
            self.model = KMSStatusReport
            self.pdf = StatusReportPDF
        elif self.model_name == 'historical_report':
            self.model = KMSHistoricalReport
            self.pdf = HistoricalReportPDF
        else:
            raise Exception("Invalid Model")

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)

        

        # from weasyprint import HTML
        # from common.utils.pdf import pdf_to_response

        # pdf_bytes = io.BytesIO()
        # HTML(string=render(request, 'knowledge_management_system/reports/work_report.html', {}).content).write_pdf(pdf_bytes)

        # try:
        #    return pdf_to_response(pdf_bytes)
        # except Exception:
        #    return HttpResponseNotFound()

        
        try:
            instance = self.model.objects.prefetch_related('prospect_tags').get(id=id)
            filename = f"{self.model_name.title()}_{instance.name.title()}.pdf"
        
            model_pdf = self.pdf(instance, filename)
        
            return model_pdf.to_http_response()
        except self.model.DoesNotExist:
            return HttpResponseNotFound()


@has_project_permission()
def get_kms_target_map(request, project: Project, slug, target):
    """Retrieves the Tenements in JSON format from a Project's Dashboard. """
    targets = project.targets.all()
    # get the permit type and number to be displayed on project map
    context = serialize("geojson", project.tenements.all(), geometry_field="area_polygons",
                        fields=["permit_type", "permit_number", "permit_status", "date_lodged", "date_granted",
                                "ahr_name"])

    coordinates = [{
        'name': target.name,
        'description': target.description,
        'location': target.location,  # target.location,
    } for target in targets]
    # Send it off
    return render(request, "interactive_map/project_map.html",
                  {'context': context,
                   'targets': json.dumps(coordinates, default=str),
                   }, content_type='application/json')


def pdf(request, slug):
    return render(request, "knowledge_management_system/pdf_reader.html", {})


def get_pdf(request, slug):
    from common.utils.pdf import DemoPDF

    return DemoPDF().to_http_response()

def upload_image(request, slug):
    if request.method == "POST":
        try:
            file = request.FILES['file']
            file_name_suffix = file.name.split(".")[-1]
            if file_name_suffix not in ["jpg", "png", "gif", "jpeg", ]:
                return JsonResponse({"message": "wrong type"})
            upload_file = MediaFile(file=file,file_path="kms/" + slug, filename=file.name, tag=MediaFile.DATASET)
            upload_file.save()

            return JsonResponse({"location":"http://" + request.get_host() + settings.MEDIA_URL + str(upload_file.file)})
        except Exception as e:
            print(e)

def update_html_with_images(html_content, post_data):
    soup = BeautifulSoup(html_content, 'html.parser')
    img_tags = soup.find_all('img')

    for img in img_tags:
        src = img.get('src')
        if src in post_data:
            img['src'] = post_data[src]
    updated_content = str(soup)
    return updated_content

def update_html_with_images_from_files(html_content, request_files):
    soup = BeautifulSoup(html_content, 'html.parser')
    img_tags = soup.find_all('img')

    for img in img_tags:
        src = img.get('src')
        if src in request_files:
            image_file = request_files[src]
            if image_file:
                image_content = image_file.read()
                base64_encoded = base64.b64encode(image_content).decode('utf-8')
                img['src'] = f"data:{image_file.content_type};base64,{base64_encoded}"

    updated_content = str(soup)
    return updated_content
@has_project_permission()
def get_tasks(request, project: Project, slug):
    tasks = TenementTask.objects.filter(tenement__project=project).prefetch_related('files').all()
    context = {
        'data': [task.as_table_row() for task in tasks]
    }

    return JsonResponse(context, status=HTTPStatus.OK)