from django.apps import apps

from common.management.commands.base.threaded import AbstractProgressCommand


class Command(AbstractProgressCommand):

    help = (
        "Empties a database table by app and model names in batches. CASCADE will be triggered appropriately. "
        "Many-to-many relationships must still be deleted manually."
    )

    def __init__(self):
        super().__init__()
        self._progress = 0
        self._length = 0
        self._size = 0

    @property
    def progress(self) -> int:
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value

    @property
    def length(self) -> int:
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def add_arguments(self, parser):
        # Base arguments
        parser.add_argument('app', type=str, help='Application name')
        parser.add_argument('model', type=str, help='Model name')
        parser.add_argument('--batch', '-b', type=int, default=self.size, help='Number of records deleted per batch.')

    def handle(self, *args, **options):
        # Get the model
        app_name = options['app']
        model_name = options['model']
        model = apps.get_model(app_name, model_name)

        # Get counts
        self.progress = 0
        self.size = options.get('batch', 200)
        self.length = model.objects.count()

        # While the table has contents, delete everything in batches.
        while model.objects.exists():
            current_size = model.objects.count()
            size = min(self.size, current_size)
            objs = model.objects.all()[:size]

            for obj in objs:
                obj.delete()
                self.progress += 1
                self.print_progress_bar(self.progress, self.length)