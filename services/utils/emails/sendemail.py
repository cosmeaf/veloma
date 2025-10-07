# services/utils/emails/sendemail.py
from __future__ import annotations
from typing import Sequence, Optional, Dict, Any, Tuple
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from services.models import ServiceToggle, EmailProvider

class EmailServiceError(Exception):
    pass

class EmailService:
    SERVICE_KEY = "email"

    def __init__(self, url_key: Optional[str] = None):
        self.url_key = url_key  # reservado para roteamento futuro

    # -------- Public API --------
    def send_by_template(
        self,
        template_code: str,                 # ex.: "welcome" → emails/welcome.html|txt
        to: Sequence[str],
        context: Optional[Dict[str, Any]] = None,
        *,
        from_email: Optional[str] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
        reply_to: Optional[Sequence[str]] = None,
        attachments: Optional[Sequence[Tuple[str, bytes, str]]] = None,
        subject: Optional[str] = None,
    ) -> str:
        self._guard_enabled()

        ctx = context or {}
        txt_name = f"emails/{template_code}.txt"
        html_name = f"emails/{template_code}.html"

        body_text = self._safe_render(txt_name, ctx) or ""
        body_html = self._safe_render(html_name, ctx)
        final_subject = subject or ctx.get("subject") or f"[{template_code}]"

        if not body_text and body_html:
            body_text = strip_tags(body_html)

        return self._deliver(
            subject=final_subject,
            body_text=body_text,
            body_html=body_html,
            to=to,
            from_email=from_email,
            cc=cc, bcc=bcc, reply_to=reply_to, attachments=attachments
        )

    def send_raw(
        self,
        subject: str,
        to: Sequence[str],
        *,
        body_text: str = "",
        body_html: Optional[str] = None,
        from_email: Optional[str] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
        reply_to: Optional[Sequence[str]] = None,
        attachments: Optional[Sequence[Tuple[str, bytes, str]]] = None,
    ) -> str:
        self._guard_enabled()
        if not body_text and body_html:
            body_text = strip_tags(body_html)
        return self._deliver(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            to=to,
            from_email=from_email,
            cc=cc, bcc=bcc, reply_to=reply_to, attachments=attachments
        )

    # -------- Internals --------
    def _safe_render(self, template_name: str, context: Dict[str, Any]) -> Optional[str]:
        try:
            return render_to_string(template_name, context)
        except Exception:
            return None

    def _guard_enabled(self) -> None:
        t = ServiceToggle.objects.filter(key=self.SERVICE_KEY).first()
        if t and not t.enabled:
            raise EmailServiceError("Email service is disabled")

    def _resolve_provider(self) -> EmailProvider:
        prov = EmailProvider.objects.filter(is_default=True).first() or EmailProvider.objects.first()
        if prov:
            return prov
        # fallback console
        return EmailProvider(
            name="Console (fallback)",
            code="console_fallback",
            provider="console",
            from_email_default=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
        )

    def _build_backend_params(self, prov: EmailProvider) -> tuple[str, dict]:
        if prov.provider == "console":
            return ("django.core.mail.backends.console.EmailBackend", {})
        if prov.provider == "filebased":
            path = prov.file_path or getattr(settings, "EMAIL_FILE_PATH", None)
            if not path:
                raise EmailServiceError("filebased backend requer file_path")
            return ("django.core.mail.backends.filebased.EmailBackend", {"file_path": path})
        # SMTP padrão
        use_ssl = bool(prov.use_ssl)
        return ("django.core.mail.backends.smtp.EmailBackend", {
            "host": prov.host,
            "port": prov.port,
            "username": prov.username or None,
            "password": prov.password or None,
            "use_tls": bool(prov.use_tls) and not use_ssl,
            "use_ssl": use_ssl,
            "timeout": prov.timeout or 30,
        })

    def _deliver(
        self,
        *,
        subject: str,
        body_text: str,
        body_html: Optional[str],
        to: Sequence[str],
        from_email: Optional[str],
        cc: Optional[Sequence[str]],
        bcc: Optional[Sequence[str]],
        reply_to: Optional[Sequence[str]],
        attachments: Optional[Sequence[Tuple[str, bytes, str]]],
    ) -> str:
        prov = self._resolve_provider()
        backend_path, backend_kwargs = self._build_backend_params(prov)
        connection = get_connection(backend=backend_path, **backend_kwargs)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=body_text or "",
            from_email=from_email or prov.from_email_default or getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=list(to),
            cc=list(cc) if cc else None,
            bcc=list(bcc) if bcc else None,
            reply_to=list(reply_to) if reply_to else None,
            connection=connection,
        )
        if body_html:
            msg.attach_alternative(body_html, "text/html")
        if attachments:
            for name, content, mimetype in attachments:
                msg.attach(name, content, mimetype)

        msg.send(fail_silently=False)
        return subject
