import os

from django.urls import path, re_path, include
from django.conf import settings
from django.contrib.auth import views as auth_views

from project.models import Permission
from . import views
from project.utils import post as project_post

from .utils import post
from interactive_map import views as im_views

app_name = "kms"

PROJECT_BASE = '<str:slug>/'
PROSPECT_BASE = PROJECT_BASE + 'prospect/<uuid:target>/'

urlpatterns = [
    path(PROJECT_BASE, views.ProjectView.as_view(), name='project_page'),
    path(PROJECT_BASE + 'edit', views.ProjectFieldView.as_view(), name='project_cms'),
    path(PROJECT_BASE + 'form/<str:model_name>/<int:id>', views.FormView.as_view(), name='project_form'),
    path(PROJECT_BASE + 'form/<str:model_name>', views.FormView.as_view(), name='project_form'),
    path(PROJECT_BASE + 'model/<str:model_name>', views.SerializeDatatable.as_view(), name='project_model'),

    path(PROSPECT_BASE, views.ProspectView.as_view(), name='prospect_page'),
    path(PROSPECT_BASE + 'edit', views.ProspectFieldView.as_view(), name='prospect_cms'),
    path(PROSPECT_BASE + 'form/<str:model_name>', views.FormView.as_view(), name='prospect_form'),
    path(PROSPECT_BASE + 'model/<str:model_name>', views.SerializeDatatable.as_view(), name='prospect_model'),

    path(PROJECT_BASE + 'get/tenements_json/', views.get_tenements_json, name='get_tenements_json'),
    path(PROSPECT_BASE + 'get/tenements_json/', views.get_tenements_json),
    path(PROJECT_BASE + 'get/kms_target_map/<str:target>', views.get_kms_target_map, name='get_kms_target_map'),
    path(PROJECT_BASE + 'get/report/<str:model_name>/<int:id>', views.GetReportsView.as_view(), name='get_report'),
    path(PROJECT_BASE + 'post/task/add/', project_post.add_task, name='task_add'),
    path(PROJECT_BASE + 'post/task/delete/', project_post.delete_task, name='task_delete'),
    path(PROJECT_BASE + 'get/tasks/', views.get_tasks, name='get_tasks'),


    path(PROJECT_BASE + 'pdf/', views.pdf, name='pdf'),
    path(PROJECT_BASE + 'get/pdf', views.get_pdf, name='get_pdf'),

    path(PROJECT_BASE + 'upload/image/', views.upload_image, name='upload_image'),

    path(PROJECT_BASE + 'post/target/add/', post.add_target, name='add_target'),

]
