from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_frontend_groups(sender, **kwargs):
    if sender.label != 'veloma_authentication':
        return
    Group.objects.get_or_create(name='STAFF')
    Group.objects.get_or_create(name='USER')
