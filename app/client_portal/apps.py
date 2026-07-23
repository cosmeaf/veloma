from django.apps import AppConfig


class ClientPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.client_portal'
    label = 'veloma_client_portal'
    verbose_name = 'Client portal'

    def ready(self):
        from . import signals  # noqa: F401
