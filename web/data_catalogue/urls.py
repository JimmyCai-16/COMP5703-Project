from django.urls import path
from . import views

app_name = 'data_catalogue'

urlpatterns = [
    path('', views.project_index, name='get_projects'),
    path('<str:slug>/', views.get_querysets, name='data_catalogue_main'),
    path('<str:slug>/files/<str:id>', views.data_catalogue_files, name='data_catalogue_files'),
    path('file_preview', views.data_catalogue_file_preview, name='file_preview'),
    path('<str:slug>/get/query/', views.get_querysets, name='get_query'),
]