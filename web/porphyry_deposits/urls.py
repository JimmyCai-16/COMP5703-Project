import os

from django.urls import path, re_path, include
from django.conf import settings
from . import views

app_name = "porphyry_deposits"

urlpatterns = [
    path('get_deposits/', views.get_deposits, name='get_deposits'),
    path('prediction/', views.prediction, name='prediction'),

 
]
