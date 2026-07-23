from rest_framework import serializers

from .models import (
    Client,
    ClientFolder,
    ClientInvitation,
    ClientMember,
    Document,
    DocumentVersion,
    Protocol,
    ProtocolComment,
    ProtocolEvent,
    ProtocolRequirement,
    ProtocolSubject,
)

# Fields the backend always sets itself; never accepted from the request.
READ_ONLY_SERVER_FIELDS = (
    'id', 'created_at', 'updated_at', 'created_by', 'uploaded_by', 'status',
    'archived_at', 'archived_by', 'archive_reason', 'deactivated_at', 'deactivated_by',
)


class ClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'legal_name', 'commercial_name', 'nif', 'entity_type', 'status', 'assigned_staff', 'created_at')
        read_only_fields = fields


class ClientDetailSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        exclude = ('deactivated_by', 'archived_by')
        read_only_fields = (
            'id', 'status', 'deactivated_at', 'deactivation_reason', 'archived_at',
            'archive_reason', 'restored_at', 'created_at', 'updated_at',
        )

    def get_member_count(self, obj):
        return obj.members.filter(status='active').count()


class ClientWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            'legal_name', 'commercial_name', 'nif', 'entity_type', 'activity_code', 'activity_description',
            'email', 'phone', 'website', 'address_line', 'postal_code', 'city', 'district', 'country',
            'accounting_period_start', 'accounting_period_end', 'assigned_staff',
        )


class ClientActionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class ClientMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = ClientMember
        fields = (
            'id', 'client', 'email', 'first_name', 'last_name', 'role', 'position', 'phone',
            'preferred_language', 'can_upload', 'can_download', 'can_view_protocols', 'can_comment',
            'can_manage_members', 'status', 'joined_at', 'created_at',
        )
        read_only_fields = ('id', 'client', 'status', 'joined_at', 'created_at')


class ClientMemberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientMember
        fields = (
            'role', 'position', 'phone', 'preferred_language', 'can_upload', 'can_download',
            'can_view_protocols', 'can_comment', 'can_manage_members',
        )


class InvitationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.legal_name', read_only=True)

    class Meta:
        model = ClientInvitation
        fields = (
            'id', 'client', 'client_name', 'email', 'role', 'status', 'invited_by',
            'expires_at', 'accepted_at', 'revoked_at', 'resend_count', 'last_sent_at', 'created_at',
        )
        read_only_fields = fields


class InvitationCreateSerializer(serializers.Serializer):
    client = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ClientMember.ROLE_CHOICES, default=ClientMember.ROLE_EMPLOYEE)


class InvitationValidateSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, trim_whitespace=False)


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)
    phone = serializers.CharField(max_length=40, required=False, allow_blank=True, default='')
    position = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    accept_terms = serializers.BooleanField()
    accept_privacy_policy = serializers.BooleanField()

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        if not attrs['accept_terms']:
            raise serializers.ValidationError({'accept_terms': 'The terms must be accepted.'})
        if not attrs['accept_privacy_policy']:
            raise serializers.ValidationError({'accept_privacy_policy': 'The privacy policy must be accepted.'})
        return attrs


class ProtocolListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.legal_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    display_status = serializers.SerializerMethodField()

    class Meta:
        model = Protocol
        fields = (
            'id', 'number', 'client', 'client_name', 'title', 'category', 'priority',
            'status', 'display_status', 'due_date', 'assigned_to', 'created_at',
            'subject', 'subject_name', 'sla_hours', 'response_due_at',
        )
        read_only_fields = fields

    def get_display_status(self, obj):
        from .selectors import is_staff_member

        request = self.context.get('request')
        if request and is_staff_member(request.user):
            return obj.status
        return obj.client_status_label


class ProtocolDetailSerializer(ProtocolListSerializer):
    class Meta(ProtocolListSerializer.Meta):
        fields = ProtocolListSerializer.Meta.fields + (
            'description', 'competence_month', 'competence_year', 'created_by',
            'started_at', 'completed_at', 'cancelled_at', 'archived_at', 'updated_at',
        )
        read_only_fields = fields


class ProtocolCreateSerializer(serializers.ModelSerializer):
    client = serializers.UUIDField()

    class Meta:
        model = Protocol
        fields = (
            'client', 'title', 'description', 'category', 'priority',
            'competence_month', 'competence_year', 'due_date', 'assigned_to',
        )


class ProtocolSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocolSubject
        fields = ('id', 'name', 'description', 'sla_hours')
        read_only_fields = fields


class OpenRequestSerializer(serializers.Serializer):
    """A client opens a request by choosing a subject; the SLA is derived from it."""

    subject = serializers.UUIDField()
    client = serializers.UUIDField(required=False)
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class ProtocolUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protocol
        fields = (
            'title', 'description', 'category', 'priority',
            'competence_month', 'competence_year', 'due_date',
        )


class ProtocolTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Protocol.STATUS_CHOICES)


class ProtocolAssignSerializer(serializers.Serializer):
    assigned_to = serializers.IntegerField()


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocolRequirement
        fields = (
            'id', 'protocol', 'title', 'description', 'category', 'required',
            'due_date', 'status', 'fulfilled_by_document', 'completed_at', 'created_at',
        )
        read_only_fields = ('id', 'protocol', 'fulfilled_by_document', 'completed_at', 'created_at')


class RequirementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocolRequirement
        fields = ('title', 'description', 'category', 'required', 'due_date')


class RequirementUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProtocolRequirement.STATUS_CHOICES)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocolComment
        fields = (
            'id', 'protocol', 'author_name_snapshot', 'message', 'visibility',
            'is_edited', 'edited_at', 'created_at',
        )
        read_only_fields = fields


class CommentCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=5000)
    visibility = serializers.ChoiceField(
        choices=ProtocolComment.VISIBILITY_CHOICES,
        default=ProtocolComment.VISIBILITY_PUBLIC,
    )


class CommentUpdateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=5000)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocolEvent
        fields = ('id', 'event_type', 'actor_name_snapshot', 'old_value', 'new_value', 'created_at')
        read_only_fields = fields


class StaffEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocolEvent
        fields = (
            'id', 'event_type', 'actor_name_snapshot', 'actor_email_snapshot', 'old_value',
            'new_value', 'metadata', 'ip_address', 'created_at',
        )
        read_only_fields = fields


class FolderSerializer(serializers.ModelSerializer):
    path = serializers.CharField(read_only=True)

    class Meta:
        model = ClientFolder
        fields = (
            'id', 'client', 'protocol', 'parent', 'name', 'slug', 'path',
            'folder_type', 'visibility', 'year', 'month', 'archived_at', 'created_at',
        )
        read_only_fields = ('id', 'slug', 'path', 'archived_at', 'created_at')


class FolderCreateSerializer(serializers.Serializer):
    client = serializers.UUIDField()
    name = serializers.CharField(max_length=180)
    parent = serializers.UUIDField(required=False, allow_null=True)
    protocol = serializers.UUIDField(required=False, allow_null=True)
    visibility = serializers.ChoiceField(
        choices=ClientFolder.VISIBILITY_CHOICES,
        default=ClientFolder.VISIBILITY_CLIENT_AND_STAFF,
    )


class FolderMoveSerializer(serializers.Serializer):
    parent = serializers.UUIDField(required=False, allow_null=True)


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = (
            'id', 'version_number', 'original_name', 'content_type', 'detected_mime_type',
            'size', 'checksum_sha256', 'uploader_name_snapshot', 'scan_status',
            'change_reason', 'created_at',
        )
        read_only_fields = fields


class DocumentSerializer(serializers.ModelSerializer):
    current_version = DocumentVersionSerializer(read_only=True)
    client_name = serializers.CharField(source='client.legal_name', read_only=True)

    class Meta:
        model = Document
        fields = (
            'id', 'client', 'client_name', 'protocol', 'folder', 'title', 'original_name',
            'category', 'status', 'visibility', 'uploader_name_snapshot', 'current_version',
            'rejection_reason', 'note', 'archived_at', 'created_at',
        )
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    client = serializers.UUIDField(required=False)
    protocol = serializers.UUIDField(required=False, allow_null=True)
    folder = serializers.UUIDField(required=False, allow_null=True)
    requirement = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    note = serializers.CharField(required=False, allow_blank=True, default='')
    visibility = serializers.ChoiceField(
        choices=Document.VISIBILITY_CHOICES,
        default=Document.VISIBILITY_CLIENT_AND_STAFF,
    )


class DocumentVersionUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    change_reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class DocumentMoveSerializer(serializers.Serializer):
    folder = serializers.UUIDField(required=False, allow_null=True)


class DocumentRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)
