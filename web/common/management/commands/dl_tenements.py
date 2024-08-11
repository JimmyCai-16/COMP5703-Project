from common.management.commands.base.threaded import BaseThreadedMultiCommand


class Command(BaseThreadedMultiCommand):
    help = 'Load Tenement and Moratorium data from ArcGIS REST Server and map to database'
    commands = [
        'scrape_qld_tenements',
        'scrape_qld_moratorium',
        # 'scrape_qld_myminesonline' one is expected to take longer since each tenement is an individual request.
        'scrape_qld_myminesonline',
    ]