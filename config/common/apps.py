from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config.common'
    label = 'veloma_configuration'
    verbose_name = 'Configuration'
