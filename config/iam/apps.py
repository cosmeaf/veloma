from django.apps import AppConfig


class IamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config.iam'
    label = 'veloma_iam'
    verbose_name = 'IAM'
