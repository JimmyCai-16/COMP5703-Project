from django.apps import AppConfig


class KnowledgeManagementSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'knowledge_management_system'

    def ready(self):
        import knowledge_management_system.signals