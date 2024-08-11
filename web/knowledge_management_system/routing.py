from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    path('ws/kms/<str:slug>/', consumers.ProjectPage.as_asgi(), name="project_websocket"),
    path('ws/kms/<str:slug>/prospect/<str:prospect>/', consumers.ProspectPage.as_asgi(), name="prospect_websocket"),
]