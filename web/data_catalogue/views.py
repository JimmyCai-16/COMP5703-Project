from http import HTTPStatus
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from project.models import Project, Permission, ProjectMember

import requests
import time
from data_catalogue.utils.ckan import solr_from_records


@login_required
def get_projects(request):
    return JsonResponse(
        Project.objects.to_datatable(request, members__user=request.user),
        status=HTTPStatus.OK
    )


@login_required
def project_index(request):
    return render(request, 'data_catalogue/data_catalogue_projects_index.html')


def data_catalogue_main(request, slug):
    return render(request, 'data_catalogue/data_catalogue_main.html', {'slug': slug})


def data_catalogue_files(request, slug, id):
    api = 'https://geoscience.data.qld.gov.au/api/action/'
    response = requests.get(api + 'package_show',
                            params={
                                'id': id,
                            })
    response_json = response.json()

    project = Project.objects.get(slug=slug)

    context = {
        'slug': slug,
        'result': response_json['result'],
        'project_name': project.name
    }

    return render(request, 'data_catalogue/data_catalogue_files.html', context=context)


def data_catalogue_file_preview(request):
    return render(request, 'data_catalogue/file_preview_page.html')

def get_querysets(request, slug):
    api = 'https://geoscience.data.qld.gov.au/api/action/'

    # Get values for queries

    ext_bbox_param = request.GET.get('ext_bbox', '')
    get_parameters = {key: request.GET.getlist(key) for key in request.GET.keys()}

    # Get query string
    solr_string_format = solr_from_records(get_parameters, exclude_fields=['ext_bbox', 'q'])

    # In case of word search
    if 'q' in get_parameters:
        solr_string_format += f' AND ({get_parameters["q"][0]})'

    # Convert the coordinates to floats
    ext_bbox_param = ext_bbox_param.split(',')
    if len(ext_bbox_param) == 4:
        ext_bbox = [float(value) for value in ext_bbox_param]
    else:
        ext_bbox = []

    # Get dataset within the geometry of the tenements on the map
    rows_per_page = 50
    start = 0
    all_results = []
    
    # while True:
    for _ in range(1): # replace with above code
        response = requests.get(api + 'package_search',
                                params={
                                    'ext_bbox': ext_bbox,
                                    'q': solr_string_format,
                                    'start': start,  # Set the starting record
                                    'rows': rows_per_page  # Number of records per page
                                })

        data = response.json()
        results = data['result']['results']

        if not results:
            break 
        
        # Remove this after pitch night
        if len(all_results) > 100:
            break

        all_results.extend(results)
        start += rows_per_page  

    project = Project.objects.get(slug=slug)
    print('result count', len(all_results))

    context = {
        'slug': slug,
        'results': all_results,
        'project': project
    }

    return render(request, 'data_catalogue/data_catalogue_main.html', context=context)