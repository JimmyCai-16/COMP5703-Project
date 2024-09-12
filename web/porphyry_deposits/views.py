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

# Receive end point cordinates to map system
def send_rectangle_coordinates(coordinates):
    Rectangle = {
        "coordinates": [
            [
                # coordinates['Point1'],  # Point 1
                # coordinates['Point2'],  # Point 2
                # coordinates['Point3'],  # Point 3
                # coordinates['Point4'],  # Point 4
                # coordinates['Point1']  # 闭合多边形回到 Point 1
                [142.03125000000003, -22.044913300245675],  # Point 1
                [142.53125000000003, -21.544913300245675],  # Point 2
                [143.03125000000003, -21.044913300245675],  # Point 3
                [144.03125000000003, -21.044913300245675],  # Point 4
                [144.53125000000003, -21.544913300245675],  # Point 5
                [144.03125000000003, -22.044913300245675],  # Point 6
                [143.03125000000003, -22.544913300245675],  # Point 7
                [142.03125000000003, -22.044913300245675]   # 闭合多边形回到 Point 1
            ]
        ],
        "permit_id": "EPM12345",  # 许可 ID
        "name": "Selected Rectangle"  # 多边形名称
    }
    # Construct a FeatureCollection in GeoJSON format
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": Rectangle['coordinates']  # 使用传入的多边形的坐标
                },
                "properties": {
                    "permit_id": Rectangle.get('permit_id', 'Unknown'),  # 可以根据需要添加更多属性
                    "name": Rectangle.get('name', 'Sample Rectangle'),  # 给多边形一个默认的名称
                }
            }
        ]
    }
    # 返回 GeoJSON 格式的响应
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

