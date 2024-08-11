from common.management.commands.base.arcgis import BaseArcGISScraper
from lms.models import Parcel, get_geometry_hash


class Command(BaseArcGISScraper):
    help = "Load Parcel data from ArcGIS REST Server and map to database"
    url = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer/4"
    model = Parcel
    geometry_field = 'geometry'
    field_map = {
        'lot': ('lot', None),
        'plan': ('plan', None),
        'tenure': ('tenure', None),
        'lot_area': ('lot_area', None),
        'exl_lot_area': ('excl_area', None),
        'lot_volume': ('lot_volume', None),
        'feature_name': ('feat_name', None),
        'alias_name': ('alias_name', None),
        'accuracy_code': ('acc_code', None),
        'surv_index': ('surv_ind', None),
        'cover_type': ('cover_typ', None),
        'parcel_type': ('parcel_typ', None),
        'locality': ('locality', None),
        'shire_name': ('shire_name', None),

        'geometry_hash': ('geometry', get_geometry_hash),

        'smis_map': ('smis_map', None),
    }
    unique_fields = ['geometry_hash']