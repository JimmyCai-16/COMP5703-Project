from common.management.commands.base.arcgis import BaseArcGISScraper
from common.utils.gis import convert_esri_time, re_findall_ids
from common.utils.model_funcs import get_choice_from_display
from native_title_management.models import NativeTitleDetermination, CLAIMANT_CHOICES, OUTCOME_CHOICES, STATUS_CHOICES, \
    METHOD_CHOICES
from tms.models import AustraliaStateChoices


class Command(BaseArcGISScraper):
    help = "Load Native Title Determinations data from ArcGIS REST Server and map to database"
    urls = [
        "https://services2.arcgis.com/rzk7fNEt0xoEp3cX/ArcGIS/rest/services/NNTT_Custodial_AGOL/FeatureServer/6"
    ]
    model = NativeTitleDetermination
    geometry_field = 'geometry'
    unique_fields = ['tribunal_number']
    field_map = {
        'tribunal_number': ('Tribunal_ID', None),
        'name': ('Name', None),
        'federal_court_number': ('FC_No', re_findall_ids),
        'federal_court_name': ('FC_Name', None),
        'date_determined': ('Determination_Date', convert_esri_time),
        'date_registered': ('NNTR_Registration_Date', convert_esri_time),
        'method': ('Determined_Method', lambda x: get_choice_from_display(METHOD_CHOICES, x)),
        'status': ('Determination_Type', lambda x: get_choice_from_display(STATUS_CHOICES, x)),
        'outcome': ('Determined_Outcome', lambda x: get_choice_from_display(OUTCOME_CHOICES, x)),
        'RNTBC_name': ('RNTBC_Name', None),
        'related_NTDA': ('Related_NTDA', re_findall_ids),
        'date_currency': ('Date_Currency', convert_esri_time),
        'NNTT_seq_no': ('NNTT_seq_no', None),
        'linked_file_no': ('Linked_File_No', None),
        'jurisdiction': ('Jurisdiction', lambda x: get_choice_from_display(AustraliaStateChoices.choices, x)),
        'claimant_type': ('Claimant_Type', lambda x: get_choice_from_display(CLAIMANT_CHOICES, x)),
        'overlap': ('Overlap', None),
    }
