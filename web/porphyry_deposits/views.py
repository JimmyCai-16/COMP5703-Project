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

@login_required
@require_POST
@csrf_protect
def get_marker_coordinates(request):
    
    # Parsing json data transmitted by the front-end
    data = request.POST
    # Retriving the geographic data
    
    geo_data = {
        'latitude': data.get('latitude'),
        'longitude': data.get('longitude')
    }
    

    print("Received coordinates: Latitude=", geo_data['latitude'], "Longitude=", geo_data['longitude'])

    response_data = {
        'message': 'Coordinates received successfully.',
        'geojson': send_marker_coordinates(geo_data)
    }
    return JsonResponse(response_data, safe=False)
    # return JsonResponse({'message': 'Coordinates received successfully.', 'geo_data': geo_data})

def send_marker_coordinates(coordinates):
    
    latitude = coordinates['latitude']
    longitude = coordinates['longitude']
    
    # Construct the Marker (polygon) using the four points and ensure it's closed
    Marker = {
        "coordinates": [longitude, latitude],  
        "permit_id": "EPM12345", 
        "name": "Selected Marker"  
    }

    # Construct a FeatureCollection in GeoJSON format
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": Marker['coordinates']  # Use the dynamically passed coordinates
                },
                "properties": {
                    "permit_id": Marker.get('permit_id', 'Unknown'),  
                    "name": Marker.get('name', 'Sample Marker') 
                }
            }
        ]
    }

    # Return the GeoJSON formatted data
    return geojson

# global_coordinates = {} #Global variables are used to pass coordinates sent by the map
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
    #print(coordinates['Point1'])
    response_data = {
        'message': 'Coordinates received successfully.',
        'geojson': send_rectangle_coordinates(coordinates)
    }
    return JsonResponse(response_data, safe=False)
    # return JsonResponse({'message': 'Coordinates received successfully.'})

# Dynamic obtaining the rectangle geo data 
def send_rectangle_coordinates(coordinates):
    
    # We expect 'coordinates' to contain Point1, Point2, Point3, Point4
    point1 = coordinates['Point1']  # [lat, lng]
    point2 = coordinates['Point2']
    point3 = coordinates['Point3']
    point4 = coordinates['Point4']

    # Construct the rectangle (polygon) using the four points and ensure it's closed
    Rectangle = {
        "coordinates": [
            [
                [point1[1], point1[0]],  # Point 1 (lng, lat)
                [point2[1], point2[0]],  # Point 2 (lng, lat)
                [point3[1], point3[0]],  # Point 3 (lng, lat)
                [point4[1], point4[0]],  # Point 4 (lng, lat)
                [point1[1], point1[0]]   # Closing the polygon back to Point 1 (lng, lat)
            ]
        ],
        "permit_id": "EPM12345",  # TODO: 这里需要修改，根据model获取预测结果再传到前端
        "name": "Selected Rectangle"  
    }

    # Construct a FeatureCollection in GeoJSON format
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": Rectangle['coordinates']  # Use the dynamically passed coordinates
                },
                "properties": {
                    "permit_id": Rectangle.get('permit_id', 'Unknown'),  
                    "name": Rectangle.get('name', 'Sample Rectangle') 
                }
            }
        ]
    }

    # Return the GeoJSON formatted data
    return geojson
    
    


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

