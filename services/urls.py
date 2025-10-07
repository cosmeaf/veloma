# services/urls.py
from django.urls import path
from .views import toggle_email, test_send

urlpatterns = [
    path("email/toggle/", toggle_email, name="services_email_toggle"),
    path("email/test/",   test_send,    name="services_email_test"),
]
