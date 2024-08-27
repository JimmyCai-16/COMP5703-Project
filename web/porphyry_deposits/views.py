from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required
def get_deposits(request):
    content = {
        'name': 'Jimmy',
        'test1': 'TEST1',
        'test2': 'TEST2',
        'test3': 'TEST3'
    }
    print("====Hello====")
    return render(request, "deposits_home.html", content)
    # return HttpResponse("This is the home view")