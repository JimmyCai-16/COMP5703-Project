from django.apps import AppConfig


class ProjectManagementConfig(AppConfig):
    name = 'project_management'

    def ready(self):
        import project_management.signals
