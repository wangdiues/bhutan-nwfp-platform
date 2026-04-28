from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.approvals'

    def ready(self):
        import apps.approvals.signals  # noqa: F401
