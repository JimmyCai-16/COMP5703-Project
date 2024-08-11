from django.urls import path

from interactive_map.views import tms
from main import settings

import interactive_map.views.main as main
import interactive_map.views.project_dashboard as project_dashboard
import interactive_map.views.lms as lms

app_name = "interactive_map"

urlpatterns = [
    # interactive map
    # path('', views.interactive_map, name = 'home'),
    
    # Polygon Data
    # path('get/tenements/', views.get_tenements_json, name = 'get_tenements_json'),
    # path('cadastre/', views.get_cadastre, name = 'cadastre'),
]

# INTERACTIVE MAP VIEWS
urlpatterns = [
    path('', main.home, name='home'),
    path('api/tenements/', main.tenements_endpoint, name='tenements'),

    # Polygon Data
    # path('get/tenements/', main.get_tenements_json, name = 'get_tenements_json'),
    # path('cadastre/', main.get_cadastre, name = 'cadastre'),
]

# PROJECT DASHBOARD END POINTS
urlpatterns += [
    path('api/project/<str:slug>/parcels/', project_dashboard.project_parcels_endpoint, name='project_parcels'),
    path('api/project/<str:slug>/prospects/', project_dashboard.project_prospects_endpoint, name='project_prospects'),
    path('api/project/<str:slug>/tenements/', project_dashboard.project_tenements_endpoint, name='project_tenements'),
]

# TMS END POINTS
urlpatterns += [
    path('api/tms/tenement/<str:permit_state>/<str:permit_type>/<str:permit_number>/tenement', tms.tenement_endpoint, name='tenement'),
    path('api/tms/tenement/<str:permit_state>/<str:permit_type>/<str:permit_number>/prospects', tms.tenement_prospects_endpoint, name='tenement_prospects'),
]


# LMS END POINTS
urlpatterns += [
    path('api/lms/<str:slug>/parcels', lms.lms_parcels_endpoint, name='lms_parcels'),
    path('api/lms/<str:slug>/parcels/<str:parcel>', lms.lms_parcels_endpoint, name='lms_parcel'),
]


if settings.DEBUG:
    urlpatterns += [
        path('testmap/<str:slug>', main.test_map, name='test_map'),
        path('lmstest/<str:slug>', lms.lms_parcels_endpoint, name='testbench'),
    ]
