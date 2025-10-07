# services/admin.py
from django.contrib import admin
from .models import ServiceToggle, EmailProvider

@admin.register(ServiceToggle)
class ServiceToggleAdmin(admin.ModelAdmin):
    list_display = ("key", "enabled")
    list_editable = ("enabled",)
    search_fields = ("key",)

@admin.register(EmailProvider)
class EmailProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "provider", "is_default")
    list_editable = ("is_default",)
    list_filter = ("provider", "is_default")
    search_fields = ("name", "code")
