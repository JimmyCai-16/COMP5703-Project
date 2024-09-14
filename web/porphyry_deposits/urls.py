import os

from django.urls import path, re_path, include
from django.conf import settings
from . import views

app_name = "porphyry_deposits"

urlpatterns = [
    path('get_deposits/', views.get_deposits, name='get_deposits'),
    path('prediction/', views.prediction, name='prediction'),
    path('validate_latitude/', views.validate_latitude, name='validate_latitude'),
    path('validate_longitude/', views.validate_longitude, name='validate_longitude'),
    path('prediction_results/', views.prediction_results, name='prediction_results'),
    path('get_marker_coordinates/', views.get_marker_coordinates, name="get_marker_coordinates"),
    path('get_rectangle_coordinates/', views.get_rectangle_coordinates, name="get_rectangle_coordinates"),
    path('send_rectangle_coordinates/', views.send_rectangle_coordinates, name="send_rectangle_coordinates")
 
]
