from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from typing import Dict
import requests
import json

from .models import PredictionData #导入预测结果数据模型
from django.db.models import Avg, Value,F,Func  # 从 django.db.models 导入
from django.db.models.functions import Cast,Coalesce
from django.db import models

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
    
    epsilon = 0.001 #0.0000000000001 #浮动范围
    # 从 coordinates 字典中提取纬度和经度，并转换为浮点数
    latitude_f = float(coordinates['latitude'])
    longitude_f = float(coordinates['longitude'])
    # 查询匹配某个误差范围内的记录
    # 生成四个角点
    # 生成四个角点（边界框的四个角）
    point1 = (latitude_f - epsilon, longitude_f - epsilon)  # 左下角
    point2 = (latitude_f + epsilon, longitude_f - epsilon)  # 左上角
    point3 = (latitude_f + epsilon, longitude_f + epsilon)  # 右上角
    point4 = (latitude_f - epsilon, longitude_f + epsilon)  # 右下角
    
    probabilityDict = get_rectangle_probability(point1,point2,point3,point4)
    
    # Construct the Marker (polygon) using the four points and ensure it's closed
    Marker = {
        "coordinates": [longitude, latitude],  
        "probability": probabilityDict['predicted_probabilities__avg'], 
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
                    "probability": Marker.get('probability', 'Unknown'),  
                    "name": Marker.get('name', 'Sample Marker') 
                }
            }
        ]
    }

    # Return the GeoJSON formatted data
    return geojson

#搜索点的概率 改用领域 废弃该函数
# def get_marker_probability(coordinates):
#     # 查询匹配这个点的记录 全取小数到8位 避免尾数不同的影响
#     # 将字符串转换为浮点数，然后再四舍五入
#     rounded_latitude = round(float(coordinates['latitude']), 8)
#     rounded_longitude = round(float(coordinates['longitude']), 8)
    
#     # 使用 Cast() 将 x 和 y 转换为 DecimalField，并使用 Coalesce() 处理可能的空值
#     try:
#         point_data = PredictionData.objects.get(x=rounded_longitude, y=rounded_latitude)
#         predicted_probability = point_data.predicted_probabilities
#         return predicted_probability

#     except PredictionData.DoesNotExist:
#         return 0


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
    
    probabilityDict = get_rectangle_probability(point1,point2,point3,point4)#计算矩形的概率
    
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
        "average_predicted_probability":probabilityDict['predicted_probabilities__avg'],  
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
                    "average_predicted_probability": Rectangle.get('average_predicted_probability', 'Unknown'), #默认值Unknow
                    "name": Rectangle.get('name', 'Sample Rectangle') 
                }
            }
        ]
    }

    # Return the GeoJSON formatted data
    return geojson

#计算矩形的概率
def get_rectangle_probability(point1,point2,point3,point4):
        # 提取所有点的纬度（lat）和经度（lng）
    latitudes = [point1[0], point2[0], point3[0], point4[0]]
    longitudes = [point1[1], point2[1], point3[1], point4[1]]
    # 计算纬度范围和经度范围
    lat_min = min(latitudes)
    lat_max = max(latitudes)
    lng_min = min(longitudes)
    lng_max = max(longitudes)

    # 查询 lng_min <= x <= lng_max 且 lat_min <= y <= lat_max 的记录并计算 predicted_probabilities 的平均值
    #aggregate() 方法返回的结果是一个字典average_probability，字典的键名是 predicted_probabilities__avg
    average_probability = PredictionData.objects.filter(x__gte=lng_min, x__lte=lng_max, y__gte=lat_min,y__lte=lat_max).aggregate(Avg('predicted_probabilities'))
    return average_probability
    
# @login_required
# def get_magnetic_map(request):
#     google_drive_file_id = '15DnUh39zr-kMh_0iK67Z8Kjnd1HZWJQ9'
#     google_drive_url = f'https://drive.google.com/uc?export=download&id={google_drive_file_id}'

#     # 使用 requests 来请求 Google Drive 文件
#     try:
#         response = requests.get(google_drive_url)
#         response.raise_for_status()  # 检查是否有错误

#         # 创建一个 HttpResponse，将文件的内容返回给前端
#         file_response = HttpResponse(response.content, content_type='application/octet-stream')
#         file_response['Content-Disposition'] = 'attachment; filename="downloaded_file.tif"'
#         print("=====", file_response, "=====")
#         return file_response

#     except requests.exceptions.RequestException as e:
#         return HttpResponse(f"Error fetching the file: {str(e)}", status=500)
    


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

