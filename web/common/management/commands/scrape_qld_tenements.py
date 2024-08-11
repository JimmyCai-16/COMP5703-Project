from common.management.commands.base.arcgis import BaseArcGISScraper
from common.utils.gis import convert_esri_time
from common.utils.model_funcs import get_choice_from_display
from tms.models import Tenement, PermitStatusChoices


class Command(BaseArcGISScraper):

    help = "Load Queensland Tenement data from ArcGIS REST Server and map to database"
    urls = [
        # Historical
        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/30",  # EPM 1991-2000
        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/35",  # EPM 2001-2010
        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/40",  # EPM 2010+

        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/65",  # EPC 1992-2000
        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/70",  # EPC 2001-2010
        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/75",  # EPC 2010+

        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/135",  # MDL Extent
        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsHistoric/MapServer/170",  # ML Extent

        # EPM
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/3',
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/2',
        # MDL
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/22',
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/25',
        # ML
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/40',
        'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/44',
    ]
    model = Tenement
    geometry_field = 'area_polygons'
    unique_fields = ['permit_state', 'permit_type', 'permit_number']
    field_map = {
        'permit_state': (None, lambda x: 'QLD'),
        'permit_type': ('permittypeabbreviation', None),
        'permit_number': ('permitnumber', None),
        'permit_name': ('permitname', None),
        'permit_status': ('permitstatus', lambda x: get_choice_from_display(PermitStatusChoices.choices, x)),
        'date_lodged': ('lodgedate', convert_esri_time),
        'date_granted': ('approvedate', convert_esri_time),
        'date_commenced': ('approvedate', convert_esri_time),
        'date_expiry': ('expirydate', convert_esri_time),
        'ahr_name': ('authorisedholdername', None),
        'prescribed_minerals': ('minerals', None),
    }