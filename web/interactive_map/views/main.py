from django.db.models import Model
from django.db.models.fields.related_descriptors import ForwardOneToOneDescriptor, ForwardManyToOneDescriptor
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render

from interactive_map.utils.core import Colour, map_api_endpoint
from interactive_map.utils.tenement import epm_pending_date_tree, epm_granted_date_tree, \
    tenement_permit_category_tree, tenements_expiring_tree, tenement_moratorium, epm_moratorium_date_tree
from lms.models import Parcel
from tms.models import Moratorium
from tms.models import Tenement


def home(request):
    return render(request, 'interactive_map/interactive_map.html', {})


@map_api_endpoint()
def tenements_endpoint(request, **kwargs):
    """/map/api/tenements/"""
    tenement_queryset = Tenement.objects.filter(permit_state='QLD')
    moratorium_queryset = Moratorium.objects.select_related('tenement').all()

    # Set up the resulting GeoJSON Tree
    tenement_geojson = [
        {
            'display': '<span class="sp-display-label" style="font-size: 13px;">Tenements</span>',
            'value': 'tenement',
            'children': [
                {
                    'display': 'Exploration Permit for Minerals (EPM)',
                    'value': 'epm',
                    'children': [
                        epm_granted_date_tree(tenement_queryset, True),
                        epm_pending_date_tree(tenement_queryset, True),
                        epm_moratorium_date_tree(moratorium_queryset)
                    ]
                },
                {
                    'display': 'Mining Development License (MDL)',
                    'value': 'mdl',
                    'children': [
                        tenement_permit_category_tree(tenement_queryset, 'MDL', 'G', Colour.MAGENTA),
                        tenement_permit_category_tree(tenement_queryset, 'MDL', 'A', Colour.BLACK),
                    ]
                },
                {
                    'display': 'Mining Lease (ML)',
                    'value': 'ml',
                    'children': [
                        tenement_permit_category_tree(tenement_queryset, 'ML', 'G', Colour.ORANGE),
                        tenement_permit_category_tree(tenement_queryset, 'ML', 'A', Colour.BROWN),
                    ]
                },
                {
                    'display': 'Exploration Permit for Coal (EPC)',
                    'value': 'epc',
                    'children': [
                        tenement_permit_category_tree(tenement_queryset, 'EPC', 'G', Colour.TEAL),
                        tenement_permit_category_tree(tenement_queryset, 'EPC', 'A', Colour.MAROON),
                    ]
                },
            ]
        }
    ]

    return JsonResponse(tenement_geojson, safe=False, status=200)

def interactive_map(request):
    return render(request, 'interactive_map/interactive_map.html', {})

def test_map(request,slug):

    context = {"slug":slug}

    for key, value in request.GET.items():
        context[key] = value
    
    return render(request, 'interactive_map/test_map.html', context)



