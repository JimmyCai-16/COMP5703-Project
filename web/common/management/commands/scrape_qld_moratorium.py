from common.management.commands.base.arcgis import BaseArcGISScraper
from common.utils.gis import convert_esri_time
from tms.models import Moratorium, Tenement


class Command(BaseArcGISScraper):
    help = "Load Moratorium data from ArcGIS REST Server and map to database"
    urls = [
        "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/MinesPermitsCurrent/MapServer/83"
    ]
    model = Moratorium
    geometry_field = 'geom'

    def __init__(self):
        # Have to define the field map here as we have a special function for tracking tenement geometry
        self.field_map = {
            'tenement': ('_geometry', self.tenement_from_geometry),
            'effective_date': ('effectivedate', convert_esri_time),
            # We need a function to convert the geometry to a tenement
        }

        # This is used to find geometry that's the same as an existing tenement
        self.tenements = Tenement.objects.order_by('date_expiry')

        # Delete all the moratoriums since there aren't any discernible unique fields
        # alternatively we could just make a hash from the geometry field, but the moratorium
        # is usually quite small so this is fine.
        Moratorium.objects.all().delete()

        super().__init__()

    def tenement_from_geometry(self, geometry):
        # Geometry may need to be transformed to a format suitable for the below comparison
        tenement = self.tenements.filter(area_polygons__exact=geometry)

        if tenement.exists():
            return tenement.first()
        else:
            return None