from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


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
    print(request.method)
    longitude = request.POST.get('longitude')
    latitude = request.POST.get('latitude')

    print(f"Longitude: {longitude}, Latitude: {latitude}")

    # Send the parameters to the model
    params = {
        'longitude': longitude,
        'latitude': latitude
    }

    # TODO: Write a new method to handle the AI-model, and then send the result to 'prediction_result.html' 

    return render(request, 'prediction_result.html', params)
