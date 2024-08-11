from common.management.commands.base.arcgis import BaseArcGISScraper
from common.utils.gis import convert_esri_time
from common.utils.model_funcs import get_choice_from_display
from native_title_management.models import APPLICATION_STATUS_CHOICES, REG_TEST_STATUS_CHOICES, NativeTitleClaimApplication
from tms.models import AustraliaStateChoices


class Command(BaseArcGISScraper):
    help = "Load Schedule of Native Title Determination Applications data from ArcGIS REST Server."
    urls = [
        "https://services2.arcgis.com/rzk7fNEt0xoEp3cX/ArcGIS/rest/services/NNTT_Custodial_AGOL/FeatureServer/8"
    ]
    model = NativeTitleClaimApplication
    geometry_field = 'geometry'
    unique_fields = ['tribunal_number']
    field_map = {
        'federal_court_number': ('FC_No', None),
        'tribunal_number': ('Tribunal_ID', None),
        'name': ('Name', None),
        'date_lodged': ('Date_Lodged', convert_esri_time),
        'date_status_effective': ('Date_Lodged', convert_esri_time),
        'status': ('Status', lambda x: get_choice_from_display(APPLICATION_STATUS_CHOICES, x)),
        'sub_status': ('RT_Status', lambda x: get_choice_from_display(REG_TEST_STATUS_CHOICES, x)),
        'date_registered': ('Date_RT_Decision', convert_esri_time),
        'representative': ('Representative', None),
        'jurisdiction': ('Jurisdiction', lambda x: get_choice_from_display(AustraliaStateChoices.choices, x)),
        'overlap': ('Overlap', None),
    }
