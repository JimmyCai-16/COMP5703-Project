from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from typing import Dict
import json


# Create your views here.

@login_required
def get_deposits(request):
    content = {
        'name': 'Jimmy',
        'test1': 'TEST1',
        'test2': 'TEST2',
        'test3': 'TEST3',
        'test4': 'TEST4'
    }
    print("====Hello====")
    return render(request, "deposits_home.html", content)
    # return HttpResponse("This is the home view")

@login_required
@require_POST
def prediction(request):
    # print(request.method)
    longitude = request.POST.get('longitude')
    latitude = request.POST.get('latitude')

    # Send the parameters to the model
    params = {
        'longitude': longitude,
        'latitude': latitude
    }
    
    return render(request, 'prediction_result.html', params)

# Validate the user input form
# Dual authentication to prevent users from overstepping front-end authentication
@login_required
@require_POST
def validate_latitude(request):
    latitude = request.POST.get('latitude')

    errors = {}
    if latitude and not is_valid_latitude(latitude):
        errors['latitude'] = 'Invalid latitude value.'

    context = {
        'errors': errors
    }

    print("errors: ", errors)

    return render(request, 'utils/error_message.html', context)

# Dual authentication to prevent users from overstepping front-end authentication
@login_required
@require_POST
def validate_longitude(request):
    longitude = request.POST.get('longitude')
    latitude = request.POST.get('latitude')

    errors = {}
    if longitude and not is_valid_longitude(longitude):
        # Note that the names should correspond
        errors['longitude'] = 'Invalid longitude value.'

    context = {
        'errors': errors
    }

    print("errors: ", errors)

    return render(request, 'utils/error_message.html', context)

@login_required
def prediction_results(request):
    
    longitude = request.POST.get('longitude')
    latitude = request.POST.get('latitude')

    context = {
        'longitude': longitude,
        'latitude': latitude,
    }
    
    # TODO: Write a new method to handle the AI-model, and then send the result to 'prediction_result.html' 

    
    return render(request, 'prediction_result.html', context)

# TODO: 不知道为什么，点击一次会发送好多次请求 -> Done 在前端解决了这个问题，防止提交多个layer
@login_required
@require_POST
@csrf_protect
def get_circle_coordinates(request):
    
    # Parsing json data transmitted by the front-end
    data = request.POST
    # Retriving the geographic data
    
    geo_data = {
        'latitude': data.get('latitude'),
        'longitude': data.get('longitude')
    }

    print("Received coordinates: Latitude=", geo_data['latitude'], "Longitude=", geo_data['longitude'])

    return JsonResponse({'message': 'Coordinates received successfully.', 'geo_data': geo_data})

# Process rectangle drawing
@login_required
@require_POST
@csrf_protect
def get_rectangle_coordinates(request):
    
    # Retriving the data sent from the frontend
    data = json.loads(request.body.decode('utf-8'))
    coordinates = data.get('coordinates', {})    

    # Iterate through each point and print out the corresponding coordinates
    for kv in coordinates:
        print(kv, ":", "Lat:", coordinates[kv][0], ",", " Lng:", coordinates[kv][1])
        
    return JsonResponse({'message': 'Coordinates received successfully.'})


    

def is_valid_longitude(value):
    try:
        lon = float(value)
        return -180 <= lon <= 180
    except ValueError:
        return False

def is_valid_latitude(value):
    try:
        lat = float(value)
        return -90 <= lat <= 90
    except ValueError:
        return False

