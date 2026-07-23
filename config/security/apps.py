from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config.security'
    label = 'veloma_security'
    verbose_name = 'Security'
