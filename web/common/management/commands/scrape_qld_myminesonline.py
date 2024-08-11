import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from math import ceil

import requests
from django.core.paginator import Paginator, EmptyPage

from common.management.commands.base.threaded import BaseThreadedScraperCommand
from common.utils.common import try_get_json, ANSI
from main.utils.django_date import try_get_datetime
from tms.models import Tenement, PermitStatusChoices
from tms.utils.scraper import try_find_choice


class Command(BaseThreadedScraperCommand):
    help = (
        "Scrapes tenement data from MyMinesOnline. This process is relatively slow as a request must be made for each"
        "individual tenement."
    )

    model = Tenement

    def __init__(self):
        super().__init__()
        self.paginator = None
        self._batch_size = 100

    @property
    def length(self) -> int:
        return self.paginator.count

    @length.setter
    def length(self, value):
        raise ValueError("Unable to modify length as it is set by paginator.")

    @property
    def count(self) -> int:
        return self.paginator.num_pages

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @staticmethod
    def get_obj_url(obj):
        """Returns the MyMinesOnline url for the specific object."""
        return f"https://myminesonlineservices.business.qld.gov.au/Web/Api/PublicEnquiryReport/{obj.permit_type}/{obj.permit_number}"

    def setup(self, *args, **options):
        # Create the paginator for the model for batching
        self.paginator = Paginator(self.model.objects.all(), self.size)

        # Print thread information
        self.stdout.write(f'Scraping: https://myminesonlineservices.business.qld.gov.au/ {ANSI.RED}Note: Slow Process{ANSI.RESET}', ending=' ')
        self.stdout.write(f"(w: {self.workers} b: {self.size} n: {self.count})")

    def thread(self, n, *args, **options):
        try:
            # Access the Nth page and iterate through each item
            page = self.paginator.page(n)

            instances_to_update = []
            for tenement in page:
                if self.interrupted:  # Check for interrupted thread.
                    break

                # Request the data for this specific tenement
                url = self.get_obj_url(tenement)
                data = try_get_json(url)

                if data:
                    # Get data from myminesonline
                    permit_info = data.get('PermitSection', {})
                    native_title = data.get('NativeTitleSection', {})
                    holder_info = data.get('HoldersSection', {})
                    area = data.get('AreaSection', {})
                    purpose_minerals = data.get('PurposeAndMineralsSection', {})
                    financials = data.get('FinancialsSection', {})
                    ahr_info = holder_info.get('AHR', {})
                    area_details = area.get('AreaDetails', {})

                    # Map the myminesonline data to a dict
                    obj_map = {
                        'permit_name': permit_info.get('PermitName'),
                        'permit_status': try_find_choice(PermitStatusChoices, permit_info.get('PermitStatusTypeDescription')),

                        'date_lodged': try_get_datetime(permit_info.get('DateLodged')),
                        'date_granted': try_get_datetime(permit_info.get('ApproveDate')),
                        'date_commenced': try_get_datetime(permit_info.get('CommenceDate')),
                        'date_expiry': try_get_datetime(permit_info.get('ExpiryDate')),
                        'date_renewed': None,  # try_get_datetime(permit_info.get('ExpiryDate')),

                        'ahr_name': ahr_info.get('Name'),
                        'ahr_address': ahr_info.get('Address'),
                        'ahr_email': ahr_info.get('Email'),
                        'ahr_mobile_number': ahr_info.get('MobilePhone'),
                        'ahr_phone_number': ahr_info.get('Phone'),

                        'area_units': area_details.get('Area', {}).get('Area', None),
                        'area_label': area_details.get('Area', {}).get('Unit', None),
                        'area_exclusions': area_details.get('Exclusions'),
                        'area_locality': area_details.get('Locality'),
                        'area_local_authority': area_details.get('LocalAuthority'),
                        'area_mining_district': area_details.get('MiningDistrict'),

                        'prescribed_minerals': [
                            # The prescribed minerals are in a weird nested dict, lets consolidate them into a simple list
                            sub[key] for sub in purpose_minerals.get('SoughtMinerals', {}).get('Minerals', [])
                            for key in sub
                        ],
                        'rent_rate': financials.get('RentRate'),
                        'native_title_description': None,  # native_title.get('Description'),
                        'native_title_outcome': None,  # native_title.get('Outcome'),
                        'native_title_parties': None,  # native_title.get('Parties'),
                        'native_title_process': native_title.get('CurrentNT'),
                        # 'native_title_date_start': None,  # native_title.get('StartDate'),
                    }

                    # Update the model from the data
                    for field, value in obj_map.items():
                        setattr(tenement, field, value)

                    # Save the tenement and increase the progress
                    instances_to_update.append(tenement)

                # Increase progress per object
                self.progress += 1

            # Update all the objects
            self.model.objects.bulk_update(instances_to_update)

        except EmptyPage:
            return
