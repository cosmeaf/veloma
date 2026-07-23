from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config.authentication'
    label = 'veloma_authentication'
    verbose_name = 'Authentication'

    def ready(self):
        from . import signals  # noqa: F401
