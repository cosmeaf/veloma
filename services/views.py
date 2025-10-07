# services/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import ServiceToggle
from .serializers import EmailTestSerializer
from .utils.emails.sendemail import EmailService

@api_view(["POST"])
@permission_classes([IsAdminUser])
def toggle_email(request):
    enabled = bool(request.data.get("enabled", True))
    obj, _ = ServiceToggle.objects.get_or_create(key="email", defaults={"enabled": enabled})
    if obj.enabled != enabled:
        obj.enabled = enabled
        obj.save(update_fields=["enabled"])
    return Response({"key": obj.key, "enabled": obj.enabled})

@api_view(["POST"])
@permission_classes([IsAdminUser])
def test_send(request):
    s = EmailTestSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    data = s.validated_data
    svc = EmailService()
    if data.get("template_code"):
        msgid = svc.send_by_template(
            template_code=data["template_code"],
            to=data["to"],
            context=data.get("context") or {},
            subject=data.get("subject"),
        )
    else:
        msgid = svc.send_raw(
            subject=data.get("subject") or "(no subject)",
            to=data["to"],
            body_text=data.get("body_text") or "",
            body_html=data.get("body_html"),
        )
    return Response({"status": "ok", "message_id": msgid}, status=status.HTTP_200_OK)
