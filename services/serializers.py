# services/serializers.py
from rest_framework import serializers

class EmailTestSerializer(serializers.Serializer):
    to = serializers.ListField(child=serializers.EmailField(), allow_empty=False)
    template_code = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.CharField(required=False, allow_blank=True)
    context = serializers.DictField(required=False)
    body_text = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.CharField(required=False, allow_blank=True)
