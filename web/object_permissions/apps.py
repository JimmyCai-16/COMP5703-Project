from django.apps import AppConfig


class ObjectPermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'object_permissions'

    def ready(self):
        import object_permissions.signals
