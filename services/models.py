# services/models.py
from django.db import models

class ServiceToggle(models.Model):
    """
    Liga/Desliga serviços transversais por chave (ex.: 'email').
    """
    key = models.CharField(max_length=50, unique=True)
    enabled = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.key} → {'ON' if self.enabled else 'OFF'}"


class EmailProvider(models.Model):
    """
    Configurações de envio. Uma linha pode ser marcada como default.
    """
    PROVIDER_CHOICES = [
        ("smtp", "Generic SMTP"),
        ("console", "Django Console"),
        ("filebased", "Django File-Based"),
    ]
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True)  # ex.: "default"
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="smtp")
    is_default = models.BooleanField(default=True)

    # SMTP:
    host = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(default=587)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    timeout = models.PositiveIntegerField(default=30)

    # File-based:
    file_path = models.CharField(max_length=255, blank=True)

    from_email_default = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code}){' *' if self.is_default else ''}"
