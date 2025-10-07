from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
# lê todas as settings que começam com CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")
# descobre tasks.py em todos os apps de INSTALLED_APPS
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
