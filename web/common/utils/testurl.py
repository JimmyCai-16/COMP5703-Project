import json

from django.core.management import BaseCommand
from typing import Union

from common.utils.common import try_get_json, try_get_request


def op_join(fields, operator: str = 'AND'):
    """Joins an iterable by an operator."""
    return f" {operator} ".join(fields)


def solr_from_field_value(field: str, value: Union[str, list], operator: str = 'AND'):
    """Generates a generic SOLR string from a field and value item."""
    if isinstance(value, str):
        value = [value]

    if value[0] is None:
        return None

    joined_solr = op_join([f'{field}:{v}' for v in value], operator)

    return f'({joined_solr})'


def solr_from_records(records, exclude_fields=None):
    """Generates a SOLR string from a dictionary in key value format. Fields should have associated 'operator'
    field e.g., for 'type' you might have 'type_operator'."""
    solr_strs = []

    if not exclude_fields:
        exclude_fields = []

    for field, value in records.items():
        if field.endswith('_operator') or field in exclude_fields:
            # Skip operator fields
            continue

        operator = ''.join(records.get(field + '_operator', ['AND']))

        solr_str = solr_from_field_value(field, value, operator)

        if solr_str:
            solr_strs.append(solr_str)

    return op_join(solr_strs, 'AND')


class CKANAPI:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def _make_request(self, endpoint, params=None):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = self.api_key

        try:
            response = try_get_request(f"{self.base_url}/{endpoint}", params=params, headers=headers)
        except ConnectionError as e:
            raise Exception(f"Failed to fetch data from CKAN API.")

        return response.json()

    def group_list(self):
        """List all datasets on CKAN."""
        endpoint = 'api/3/action/group_list'
        return self._make_request(endpoint)

    def package_list(self):
        """List all datasets on CKAN."""
        endpoint = 'api/3/action/package_list'
        return self._make_request(endpoint)

    def package_show(self, dataset_id):
        """Get details of a specific dataset by ID."""
        endpoint = f'api/3/action/package_show'
        params = {'id': dataset_id}
        return self._make_request(endpoint, params=params)

    def package_search(self, query):
        """Search for datasets matching a specific query."""
        endpoint = 'api/3/action/package_search'
        return self._make_request(endpoint, params=query)

    def recent_data(self, query):
        endpoint = 'api/3/action/recently_changed_packages_activity_list'
        return self._make_request(endpoint, params=query)



# GeoJSONextent             = 'geom'  # "{\"type\":\"Polygon\",\"coordinates\":[[[143.501139501025,-19.5817888591227],[143.501139476886,-19.5984555522604],[143.501139453748,-19.615122245398],[143.501139429609,-19.6317889385356],[143.501139405471,-19.6484556316732],[143.501139433332,-19.6651223148109],[143.501139459192,-19.6817889969484],[143.501139487052,-19.698455679086],[143.501139513913,-19.7151223632235],[143.517806115636,-19.7151222172465],[143.534472717359,-19.7151220732706],[143.551139320082,-19.7151219272959],[143.551139360938,-19.7317886154334],[143.551139401794,-19.748455302571],[143.551139442649,-19.7651219897085],[143.551139483505,-19.781788677846],[143.551139524359,-19.7984553649835],[143.551139617214,-19.815122053121],[143.551139709068,-19.8317887412584],[143.534473080354,-19.831788871233],[143.51780645064,-19.8317890012087],[143.501139820926,-19.8317891311856],[143.501139908784,-19.848455809323],[143.501139995642,-19.8651224874603],[143.501140082499,-19.8817891645977],[143.501140169356,-19.8984558427349],[143.501140256213,-19.9151225198723],[143.50114034407,-19.9317891980095],[143.484473703364,-19.9317893089875],[143.467807063658,-19.9317894189666],[143.451140422952,-19.9317895299469],[143.434473569246,-19.9317898099283],[143.417806715541,-19.9317900889109],[143.401139860835,-19.9317903688946],[143.38447300713,-19.9317906478796],[143.367806152424,-19.9317909278656],[143.351139298719,-19.9317912068529],[143.334472445014,-19.9317914868413],[143.317805590309,-19.9317917668309],[143.301138736605,-19.9317920468216],[143.2844720759,-19.9317922148135],[143.267805415196,-19.9317923828066],[143.251138754491,-19.9317925498008],[143.234472093787,-19.9317927177962],[143.217805433083,-19.9317928857927],[143.201138772379,-19.9317930537905],[143.184472111675,-19.9317932217894],[143.184472076794,-19.9151265466524],[143.184472042912,-19.8984598715155],[143.18447200903,-19.8817931963785],[143.184471975148,-19.8651265222415],[143.184471941266,-19.8484598461045],[143.184471907383,-19.8317931709675],[143.1844718735,-19.8151264958304],[143.184471839617,-19.7984598206934],[143.184471864733,-19.7817931245563],[143.184471889849,-19.7651264284192],[143.184471915966,-19.748459731282],[143.201138849684,-19.748459415283],[143.217805783402,-19.7484591002851],[143.23447271912,-19.7484587832883],[143.251139652839,-19.7484584672928],[143.25113962796,-19.7317917941556],[143.251139604081,-19.7151251210183],[143.267806513802,-19.7151248160238],[143.267806475924,-19.6984581488866],[143.267806439045,-19.6817914817493],[143.251139555321,-19.6817917747438],[143.251139530441,-19.6651251026064],[143.251139505561,-19.6484584294691],[143.25113974968,-19.6317916293318],[143.251139994799,-19.6151248301945],[143.267806741529,-19.6151246041999],[143.284473489258,-19.6151243772065],[143.301140235987,-19.6151241512143],[143.317806844716,-19.6151239892232],[143.317806915841,-19.5984572730857],[143.334473518571,-19.5984571140958],[143.334473583696,-19.5817904019583],[143.334473649821,-19.5651236888208],[143.351140241555,-19.565123534832],[143.351140302681,-19.5484568246944],[143.351140361806,-19.5317901145568],[143.367806943543,-19.5317899645691],[143.384473524279,-19.5317898155826],[143.401140106016,-19.5317896655973],[143.401140062886,-19.5484563687349],[143.401140018756,-19.5651230718725],[143.41780661149,-19.5651229168883],[143.417806572359,-19.581789617026],[143.434473170092,-19.581789461043],[143.451139767825,-19.5817893040612],[143.451139794959,-19.5651226079235],[143.451139823092,-19.5484559127859],[143.467806397828,-19.5484557658052],[143.467806424963,-19.5317890716675],[143.467806451097,-19.5151223765297],[143.467806477232,-19.498455681392],[143.484473048971,-19.4984555364125],[143.501139619711,-19.498455392434],[143.517806191451,-19.4984552464567],[143.534472762191,-19.4984551024807],[143.534472741052,-19.5151217936185],[143.534472719912,-19.5317884857563],[143.534472698772,-19.548455177894],[143.534472677632,-19.5651218690318],[143.517806100897,-19.5651220170078],[143.517806079758,-19.5817887101455],[143.501139501025,-19.5817888591227]]]}",
# author                    = None,
# author_email              = None,
# commodity                 = []
# creator                   = str  # "geological-survey-of-queensland",
# creator_user_id           = 'uuid'  # "53d1baf7-cd1a-4ba3-a007-ed1195c24610",
# dataset_completion_date   = str  # "2013-04-20",
# dataset_start_date        = str  # "2012-04-21",
# earth_science_data_category = []  # ?
# extra_access_rights       = str  # "http://linked.data.gov.au/def/data-access-rights/open",
# extra_contact_uri         = str  # "GSQOpenData@dnrme.qld.gov.au",
# extra_identifier          = str  # "CR128121",
# georesource_report_type   = str  # "http://linked.data.gov.au/def/georesource-report/permit-report-annual",
# id                        = 'uuid'  # "d66104a7-6d77-4533-bc79-796baa75186b",
# isopen                    = bool  # true,
# license_id                = str  # "cc-by",
# license_title             = str  # "Creative Commons Attribution",
# license_url               = str  # "http://www.opendefinition.org/licenses/cc-by",
# maintainer                = str,
# maintainer_email          = str,
# metadata_created          = str  # "2021-11-29T02:10:03.347655",
# metadata_modified         = str  # "2021-11-29T02:10:03.347662",
# name                      = str  # "cr128121",
# notes                     = str  # "This report details work conducted over EPMs 9599, 11886, 13942, 14060 and 14209, which make up the Woolgar Project, during the 2012 to 2013 period.",
# num_resources             = int  # 7,
# num_tags                  = int  # 1,
# open_file_date            = str  # "2018-05-21",
# organization              = {...}
# owner                     = str  # "STRATEGIC MINERALS CORPORATION PTY LTD",
# owner_org                 = 'uuid'  # "1461ac2d-f813-4c97-9e3b-3900a23b0ecb",
# private                   = bool  # false,
# resource_authority_permit = str  # "EPM 11886,EPM 13942,EPM 14060,EPM 14209,EPM 9599",
# spatial                   = 'geom'  # "{\"type\":\"Polygon\",\"coordinates\":[[[143.184471839617,-19.9317932217894],[143.184471839617,-19.4984551024807],[143.551139709068,-19.4984551024807],[143.551139709068,-19.9317932217894],[143.184471839617,-19.9317932217894]]]}",
# state                     = str  # "active",
# syndicate                 = str  # "True",
# title                     = str  # "EPM9599 EPM11886 EPM13942 EPM14060 EPM14209 WOOLGAR PROJECT IN LIEU OF CR77570 ANNUAL ACTIVITY REPORT FOR PERIOD ENDING 20 APRIL 2013",
# type                      = str  # "report",
# url                       = None,
# version                   = None,
# resources                 = [],
# tags                      = [],
# groups                    = [],
# relationships_as_subject  = [],
# relationships_as_object   = [],


class Command(BaseCommand):

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('url', type=str, default=None, help='Some URL.')

    def handle(self, *args, **options):
        url = options['url']
        params = {
            'ext_date_facet': '',
            'ext_search_all': '',
            'ext_advanced_operator': 'OR',
            'ext_bbox': '',
            'ext_prev_extent': '',
            # 'q': '',
            'q': '(type:report) AND (vocab_commodity:*gold OR vocab_commodity:*tin) AND (res_format:ZIP AND res_format:XLSX)',
        }

        json_data = {
            'ext_bbox': [
                '139.65820312500003,-23.200960808078566,145.76660156250003,-18.583775688370928'
            ],
            'type': ['report'],
            'vocab_commodity': ['*gold', '*tin'],
            'res_format': ['PDF', 'JSON'],
            'vocab_earth_science_data_category': [''],
            'georesource_report_type': [''],
            'type_operator': ['AND'],
            'vocab_commodity_operator': ['OR'],
            'res_format_operator': ['AND'],
            'vocab_earth_science_data_category_operator': ['AND'],
            'georesource_report_type_operator': ['AND'],
        }

        ext_bbox = json_data.get('ext_bbox', [''])[0]
        test_solr_string = solr_from_records(json_data, exclude_fields='ext_bbox')

        params = {
            'ext_date_facet': '',
            'ext_search_all': '',
            'ext_advanced_operator': 'OR',
            'ext_prev_extent': '',
            # 'ext_bbox': ext_bbox,
            'ext_bbox': '',
            'q': test_solr_string
        }

        print(url, params)

        ckan = CKANAPI(url)
        datasets = ckan.package_search(params)

        with open("test.json", "w") as file:
            file.write(json.dumps(datasets))

        """
        response = requests.get('https://geoscience.data.qld.gov.au/api/3/action/' + 'package_search',
               params={
                   'ext_bbox':[148.7, -26.6, 148.9, -26.5],
                   'fq':[
                       'type:report',
                       'earth_science_data_category:geochemistry'
                   ]
       })"""
