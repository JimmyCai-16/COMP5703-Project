import hashlib
import json
import multiprocessing
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from math import ceil

import requests
from django.contrib.gis.geos import GEOSGeometry
from django.core.management import call_command

from common.management.commands.base.threaded import BaseThreadedScraperCommand
from common.utils.common import try_get_json, ANSI


class BaseArcGISScraper(BaseThreadedScraperCommand):
    help = (
        "Scrapes an ArcGIS REST API server into a database model. "
        "Many-to-many relationships must still be handled manually."
    )

    geometry_field = 'geometry'

    def setup(self, *args, **options):
        """Sets up the process length and size by querying the target server. May need to be reworked for different
        servers."""
        # Update the values
        self.progress = 0

        # Get the counts and batch sizes from the server
        self.length = try_get_json(
            self.url + '/query',
            params={'where': '1=1', 'returnCountOnly': True, 'f': 'json'}
        ).get('count', 1)

        self.size = try_get_json(
            self.url,
            params={'f': 'pjson'}
        ).get('maxRecordCount', 1)

        # Optimize the thread parameters
        if options['optimize']:
            self.optimize_parameters()

        # Print thread information
        self.stdout.write(f'Scraping: {self.url}', ending=' ')
        self.stdout.write(f"(w: {self.workers} b: {self.size} n: {self.count})")

    def thread(self, n, *args, **options):
        # Build the querystring to get the GeoJSON
        result_offset = n * self.size
        params = {
            'where': '1=1',
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'units': 'esriSRUnit_Meter',
            'outFields': '*',
            'returnGeometry': True,
            'f': 'geojson',
            'resultOffset': result_offset,
            'resultRecordCount': self.size,
        }

        # Get the feature data from the GIS server
        data = try_get_json(self.url + '/query', params=params)
        features = data.get('features', [])

        # De-serialize all the features using the supplied feature map
        for feature in features:
            if self.interrupted:  # Check for interrupted thread.
                return

            properties = feature['properties']
            geometry = feature['geometry']

            geos_geometry = GEOSGeometry(json.dumps(geometry))

            # Property stores
            unique_properties = {}
            mapped_properties = {
                self.geometry_field: geos_geometry,
            }

            for key_to, (key_from, func) in self.field_map.items():
                if key_from == self.geometry_field:
                    value = geos_geometry
                else:
                    value = properties.get(key_from)

                # If the property is a function then call it to get the result
                if callable(func):
                    value = func(value)

                if key_to in self.unique_fields:
                    unique_properties[key_to] = value
                else:
                    mapped_properties[key_to] = value

            # Create the models, use unique properties to update existing elements
            if unique_properties:
                self.model.objects.update_or_create(**unique_properties, defaults=mapped_properties)
            else:
                self.model.objects.create(**mapped_properties)

            self.progress += 1
