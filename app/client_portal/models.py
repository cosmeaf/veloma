import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from config.authentication.models import hash_token


class LifecycleStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    DEACTIVATED = 'deactivated', 'Deactivated'
    ARCHIVED = 'archived', 'Archived'


class Client(models.Model):
    """Accounting client: a company, entity or professional followed by Veloma."""

    ENTITY_TYPE_CHOICES = (
        ('quotas', 'Sociedade por quotas'),
        ('unipessoal', 'Sociedade unipessoal'),
        ('eni', 'Empresário em nome individual'),
        ('independent', 'Trabalhador independente'),
        ('association', 'Associação'),
        ('foundation', 'Fundação'),
        ('condominium', 'Condomínio'),
        ('other', 'Outro'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_name = models.CharField(max_length=255)
    commercial_name = models.CharField(max_length=255, blank=True)
    nif = models.CharField(max_length=20, unique=True, db_index=True)
    entity_type = models.CharField(max_length=32, choices=ENTITY_TYPE_CHOICES, default='quotas')
    activity_code = models.CharField(max_length=16, blank=True)
    activity_description = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    website = models.CharField(max_length=255, blank=True)
    address_line = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=2, default='PT')
    accounting_period_start = models.DateField(blank=True, null=True)
    accounting_period_end = models.DateField(blank=True, null=True)
    assigned_staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_assigned_clients',
    )
    status = models.CharField(
        max_length=16,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.ACTIVE,
        db_index=True,
    )
    deactivated_at = models.DateTimeField(blank=True, null=True)
    deactivated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_deactivated_clients',
    )
    deactivation_reason = models.CharField(max_length=255, blank=True)
    archived_at = models.DateTimeField(blank=True, null=True, db_index=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_archived_clients',
    )
    archive_reason = models.CharField(max_length=255, blank=True)
    restored_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_client'
        ordering = ('legal_name',)
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f'{self.legal_name} · {self.nif}'

    @property
    def is_active(self):
        return self.status == LifecycleStatus.ACTIVE

    @property
    def is_archived(self):
        return self.status == LifecycleStatus.ARCHIVED

    def clean(self):
        errors = {}
        digits = (self.nif or '').strip()
        if not digits.isdigit() or len(digits) != 9:
            errors['nif'] = 'The Portuguese NIF must contain exactly 9 digits.'
        self.nif = digits
        if self.accounting_period_start and self.accounting_period_end:
            if self.accounting_period_end <= self.accounting_period_start:
                errors['accounting_period_end'] = 'The period end must be later than the start.'
        if errors:
            raise ValidationError(errors)


class ClientMember(models.Model):
    """Link between a native Django user and an accounting client."""

    ROLE_OWNER = 'owner'
    ROLE_MANAGER = 'manager'
    ROLE_ACCOUNTING = 'accounting'
    ROLE_EMPLOYEE = 'employee'
    ROLE_VIEWER = 'viewer'
    ROLE_CHOICES = (
        (ROLE_OWNER, 'Owner'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_ACCOUNTING, 'Accounting'),
        (ROLE_EMPLOYEE, 'Employee'),
        (ROLE_VIEWER, 'Viewer'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='members')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='veloma_client_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    position = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    preferred_language = models.CharField(max_length=10, default='pt-pt')
    can_upload = models.BooleanField(default=True)
    can_download = models.BooleanField(default=True)
    can_view_protocols = models.BooleanField(default=True)
    can_comment = models.BooleanField(default=True)
    can_manage_members = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.ACTIVE,
        db_index=True,
    )
    joined_at = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(blank=True, null=True)
    archived_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_client_member'
        ordering = ('client__legal_name', 'user__email')
        verbose_name = 'Client member'
        verbose_name_plural = 'Client members'
        indexes = [
            models.Index(fields=('client', 'status'), name='cp_member_client_status_idx'),
            models.Index(fields=('user', 'status'), name='cp_member_user_status_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=('client', 'user'),
                condition=models.Q(status='active'),
                name='unique_active_client_member',
            ),
        ]

    def __str__(self):
        return f'{self.user.email} · {self.client.legal_name} · {self.role}'

    @property
    def is_active(self):
        return self.status == LifecycleStatus.ACTIVE


class ClientInvitation(models.Model):
    """Single-use invitation: the only way to create a USER account."""

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EXPIRED = 'expired'
    STATUS_REVOKED = 'revoked'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_REVOKED, 'Revoked'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='invitations')
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=20, choices=ClientMember.ROLE_CHOICES, default=ClientMember.ROLE_EMPLOYEE)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_sent_invitations',
    )
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_accepted_invitations',
    )
    expires_at = models.DateTimeField(db_index=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    resend_count = models.PositiveSmallIntegerField(default=0)
    last_sent_at = models.DateTimeField(blank=True, null=True)
    accepted_ip = models.GenericIPAddressField(blank=True, null=True)
    accepted_user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_client_invitation'
        ordering = ('-created_at',)
        verbose_name = 'Invitation'
        verbose_name_plural = 'Invitations'

    def __str__(self):
        return f'{self.email} · {self.client.legal_name} · {self.status}'

    @property
    def is_usable(self):
        return self.status == self.STATUS_PENDING and self.expires_at > timezone.now()

    def matches(self, token):
        return self.token_hash == hash_token(token)


class ClientFolder(models.Model):
    """Logical folder tree stored in PostgreSQL; MinIO only holds technical keys.

    The filing plan belongs to the office: only staff create, rename and move
    folders. Clients browse and deliver into them. Folders marked `staff_only`
    (and everything under them) never reach the client side.
    """

    VISIBILITY_CLIENT_AND_STAFF = 'client_and_staff'
    VISIBILITY_STAFF_ONLY = 'staff_only'
    VISIBILITY_CHOICES = (
        (VISIBILITY_CLIENT_AND_STAFF, 'Client and staff'),
        (VISIBILITY_STAFF_ONLY, 'Staff only'),
    )

    TYPE_ROOT = 'root'
    TYPE_YEAR = 'year'
    TYPE_MONTH = 'month'
    TYPE_CATEGORY = 'category'
    TYPE_PROTOCOL = 'protocol'
    TYPE_CHOICES = (
        (TYPE_ROOT, 'Root'),
        (TYPE_YEAR, 'Year'),
        (TYPE_MONTH, 'Month'),
        (TYPE_CATEGORY, 'Category'),
        (TYPE_PROTOCOL, 'Protocol'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='folders')
    protocol = models.ForeignKey(
        'Protocol',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='folders',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='children',
    )
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180)
    folder_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CATEGORY)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_CLIENT_AND_STAFF,
        db_index=True,
    )
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_created_folders',
    )
    archived_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_folder'
        ordering = ('client__legal_name', 'name')
        verbose_name = 'Folder'
        verbose_name_plural = 'Folders'
        constraints = [
            models.UniqueConstraint(fields=('client', 'parent', 'slug'), name='unique_folder_slug_per_parent'),
        ]

    def __str__(self):
        return f'{self.client.legal_name} · {self.path}'

    @property
    def path(self):
        names = [self.name]
        node = self.parent
        while node is not None:
            names.append(node.name)
            node = node.parent
        return '/'.join(reversed(names))

    @property
    def is_internal(self):
        return self.visibility == self.VISIBILITY_STAFF_ONLY

    def clean(self):
        if self.month is not None and not 1 <= self.month <= 12:
            raise ValidationError({'month': 'The month must be between 1 and 12.'})
        # Visibility is inherited: a subfolder of an internal folder is internal.
        if self.parent_id and self.parent.is_internal:
            self.visibility = self.VISIBILITY_STAFF_ONLY


class ProtocolCounter(models.Model):
    """Per-year counter used to build the public protocol number."""

    year = models.PositiveSmallIntegerField(primary_key=True)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'client_portal_protocol_counter'


class Protocol(models.Model):
    """An accounting request or process; it holds many documents."""

    STATUS_DRAFT = 'draft'
    STATUS_WAITING_DOCUMENTS = 'waiting_documents'
    STATUS_DOCUMENTS_RECEIVED = 'documents_received'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_ACTION_REQUIRED = 'action_required'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_WAITING_DOCUMENTS, 'Waiting documents'),
        (STATUS_DOCUMENTS_RECEIVED, 'Documents received'),
        (STATUS_UNDER_REVIEW, 'Under review'),
        (STATUS_ACTION_REQUIRED, 'Action required'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_ARCHIVED, 'Archived'),
    )

    # Status shown to the client, per the specification.
    CLIENT_STATUS_LABELS = {
        STATUS_DRAFT: 'Aguardando documentos',
        STATUS_WAITING_DOCUMENTS: 'Aguardando documentos',
        STATUS_DOCUMENTS_RECEIVED: 'Documentos recebidos',
        STATUS_UNDER_REVIEW: 'Em análise',
        STATUS_ACTION_REQUIRED: 'Precisamos de informações',
        STATUS_PROCESSING: 'Em processamento',
        STATUS_COMPLETED: 'Concluído',
        STATUS_CANCELLED: 'Cancelado',
        STATUS_ARCHIVED: 'Concluído',
    }

    # Allowed transitions. Reopening a completed protocol is restricted to
    # STAFF_MANAGER and enforced by the service layer.
    TRANSITIONS = {
        STATUS_DRAFT: {STATUS_WAITING_DOCUMENTS, STATUS_CANCELLED},
        STATUS_WAITING_DOCUMENTS: {STATUS_DOCUMENTS_RECEIVED, STATUS_CANCELLED},
        STATUS_DOCUMENTS_RECEIVED: {STATUS_UNDER_REVIEW, STATUS_ACTION_REQUIRED},
        STATUS_UNDER_REVIEW: {STATUS_ACTION_REQUIRED, STATUS_PROCESSING, STATUS_COMPLETED},
        STATUS_ACTION_REQUIRED: {STATUS_DOCUMENTS_RECEIVED, STATUS_UNDER_REVIEW},
        STATUS_PROCESSING: {STATUS_COMPLETED, STATUS_ACTION_REQUIRED},
        STATUS_COMPLETED: {STATUS_ARCHIVED, STATUS_UNDER_REVIEW},
        STATUS_CANCELLED: set(),
        STATUS_ARCHIVED: set(),
    }

    CATEGORY_CHOICES = (
        ('monthly_accounting', 'Contabilidade mensal'),
        ('vat', 'IVA'),
        ('irc', 'IRC'),
        ('irs', 'IRS'),
        ('payroll', 'Processamento salarial'),
        ('hr', 'Recursos humanos'),
        ('company_opening', 'Abertura de empresa'),
        ('company_closing', 'Encerramento de empresa'),
        ('corporate_change', 'Alteração societária'),
        ('tax', 'Fiscalidade'),
        ('banking', 'Bancos'),
        ('contracts', 'Contratos'),
        ('document_request', 'Pedido documental'),
        ('other', 'Outro'),
    )

    PRIORITY_LOW = 'low'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=24, unique=True, db_index=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='protocols')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_created_protocols',
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_assigned_protocols',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='other', db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    # Subject chosen by the client when opening a request; drives the SLA.
    subject = models.ForeignKey(
        'ProtocolSubject',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='protocols',
    )
    sla_hours = models.PositiveIntegerField(blank=True, null=True)
    response_due_at = models.DateTimeField(blank=True, null=True, db_index=True)
    competence_month = models.PositiveSmallIntegerField(blank=True, null=True)
    competence_year = models.PositiveSmallIntegerField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True, db_index=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    archived_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_protocol'
        ordering = ('-created_at',)
        verbose_name = 'Protocol'
        verbose_name_plural = 'Protocols'
        indexes = [
            models.Index(fields=('client', 'status'), name='cp_protocol_client_status_idx'),
            models.Index(fields=('assigned_to', 'status'), name='cp_protocol_staff_status_idx'),
        ]

    def __str__(self):
        return f'{self.number} · {self.title}'

    @property
    def client_status_label(self):
        return self.CLIENT_STATUS_LABELS.get(self.status, self.status)

    @property
    def is_open(self):
        return self.status not in {self.STATUS_COMPLETED, self.STATUS_CANCELLED, self.STATUS_ARCHIVED}

    def can_transition_to(self, status):
        return status in self.TRANSITIONS.get(self.status, set())

    def clean(self):
        if self.competence_month is not None and not 1 <= self.competence_month <= 12:
            raise ValidationError({'competence_month': 'The month must be between 1 and 12.'})


class ProtocolRequirement(models.Model):
    """A document the staff asked the client to provide."""

    STATUS_PENDING = 'pending'
    STATUS_UPLOADED = 'uploaded'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_WAIVED = 'waived'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_UPLOADED, 'Uploaded'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_WAIVED, 'Waived'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey(Protocol, on_delete=models.PROTECT, related_name='requirements')
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, blank=True)
    required = models.BooleanField(default=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    fulfilled_by_document = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='fulfilled_requirements',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_created_requirements',
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'client_portal_protocol_requirement'
        ordering = ('created_at',)
        verbose_name = 'Protocol requirement'
        verbose_name_plural = 'Protocol requirements'

    def __str__(self):
        return f'{self.protocol.number} · {self.title}'


class ProtocolEvent(models.Model):
    """Read-only protocol history."""

    # Events the client is allowed to see.
    CLIENT_VISIBLE = {
        'protocol_created',
        'status_changed',
        'due_date_changed',
        'document_requested',
        'document_uploaded',
        'document_replaced',
        'document_rejected',
        'comment_added',
        'protocol_completed',
        'protocol_reopened',
        'protocol_cancelled',
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey(Protocol, on_delete=models.PROTECT, related_name='events')
    event_type = models.CharField(max_length=48, db_index=True)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_protocol_events',
    )
    actor_name_snapshot = models.CharField(max_length=255, blank=True)
    actor_email_snapshot = models.EmailField(blank=True)
    old_value = models.CharField(max_length=255, blank=True)
    new_value = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'client_portal_protocol_event'
        ordering = ('-created_at',)
        verbose_name = 'Protocol event'
        verbose_name_plural = 'Protocol events'

    def __str__(self):
        return f'{self.protocol.number} · {self.event_type}'


class ProtocolComment(models.Model):
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_INTERNAL = 'internal'
    VISIBILITY_CHOICES = (
        (VISIBILITY_PUBLIC, 'Public'),
        (VISIBILITY_INTERNAL, 'Internal'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey(Protocol, on_delete=models.PROTECT, related_name='comments')
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_protocol_comments',
    )
    author_name_snapshot = models.CharField(max_length=255, blank=True)
    author_email_snapshot = models.EmailField(blank=True)
    message = models.TextField()
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        db_index=True,
    )
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    archived_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_protocol_comment'
        ordering = ('created_at',)
        verbose_name = 'Protocol comment'
        verbose_name_plural = 'Protocol comments'

    def __str__(self):
        return f'{self.protocol.number} · {self.visibility}'


class Document(models.Model):
    STATUS_PENDING_UPLOAD = 'pending_upload'
    STATUS_PENDING_SCAN = 'pending_scan'
    STATUS_CLEAN = 'clean'
    STATUS_INFECTED = 'infected'
    STATUS_QUARANTINED = 'quarantined'
    STATUS_REJECTED = 'rejected'
    STATUS_AVAILABLE = 'available'
    STATUS_ARCHIVED = 'archived'
    STATUS_DELETED = 'deleted'
    STATUS_CHOICES = (
        (STATUS_PENDING_UPLOAD, 'Pending upload'),
        (STATUS_PENDING_SCAN, 'Pending scan'),
        (STATUS_CLEAN, 'Clean'),
        (STATUS_INFECTED, 'Infected'),
        (STATUS_QUARANTINED, 'Quarantined'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_ARCHIVED, 'Archived'),
        (STATUS_DELETED, 'Deleted'),
    )

    VISIBILITY_CLIENT_AND_STAFF = 'client_and_staff'
    VISIBILITY_STAFF_ONLY = 'staff_only'
    VISIBILITY_CLIENT_ONLY = 'client_only'
    VISIBILITY_CHOICES = (
        (VISIBILITY_CLIENT_AND_STAFF, 'Client and staff'),
        (VISIBILITY_STAFF_ONLY, 'Staff only'),
        (VISIBILITY_CLIENT_ONLY, 'Client only'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='documents')
    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='documents',
    )
    folder = models.ForeignKey(
        ClientFolder,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='documents',
    )
    title = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    current_version = models.ForeignKey(
        'DocumentVersion',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='current_of',
    )
    category = models.CharField(max_length=32, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_SCAN,
        db_index=True,
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_CLIENT_AND_STAFF,
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_uploaded_documents',
    )
    uploader_name_snapshot = models.CharField(max_length=255, blank=True)
    uploader_email_snapshot = models.EmailField(blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    archived_at = models.DateTimeField(blank=True, null=True, db_index=True)
    # Recycle bin: a manager can delete an upload; it stays restorable until
    # purge_after, then a task removes the stored object permanently. The log
    # (who/when/why) is kept as proof even after the file is gone.
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_deleted_documents',
    )
    deleted_by_name_snapshot = models.CharField(max_length=255, blank=True)
    deletion_reason = models.CharField(max_length=255, blank=True)
    purge_after = models.DateTimeField(blank=True, null=True, db_index=True)
    purged_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_document'
        ordering = ('-created_at',)
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=('client', 'status'), name='cp_document_client_status_idx'),
            models.Index(fields=('protocol', 'status'), name='cp_document_proto_status_idx'),
        ]

    def __str__(self):
        return f'{self.title} · {self.status}'

    @property
    def is_downloadable(self):
        return self.status == self.STATUS_AVAILABLE and self.archived_at is None


class DocumentVersion(models.Model):
    SCAN_PENDING = 'pending'
    SCAN_CLEAN = 'clean'
    SCAN_INFECTED = 'infected'
    SCAN_ERROR = 'error'
    SCAN_SKIPPED = 'skipped'
    SCAN_CHOICES = (
        (SCAN_PENDING, 'Pending'),
        (SCAN_CLEAN, 'Clean'),
        (SCAN_INFECTED, 'Infected'),
        (SCAN_ERROR, 'Error'),
        (SCAN_SKIPPED, 'Skipped'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    storage_key = models.CharField(max_length=512, unique=True)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    detected_mime_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, db_index=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_uploaded_versions',
    )
    uploader_name_snapshot = models.CharField(max_length=255, blank=True)
    uploader_email_snapshot = models.EmailField(blank=True)
    scan_status = models.CharField(max_length=16, choices=SCAN_CHOICES, default=SCAN_PENDING, db_index=True)
    scan_message = models.CharField(max_length=255, blank=True)
    scanned_at = models.DateTimeField(blank=True, null=True)
    change_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'client_portal_document_version'
        ordering = ('-version_number',)
        verbose_name = 'Document version'
        verbose_name_plural = 'Document versions'
        constraints = [
            models.UniqueConstraint(fields=('document', 'version_number'), name='unique_document_version'),
        ]

    def __str__(self):
        return f'{self.document.title} · v{self.version_number}'


class DownloadAudit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='downloads')
    version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='downloads',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_document_downloads',
    )
    user_name_snapshot = models.CharField(max_length=255, blank=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='download_audits')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'client_portal_download_audit'
        ordering = ('-created_at',)
        verbose_name = 'Download audit'
        verbose_name_plural = 'Download audits'

    def __str__(self):
        return f'{self.document.title} · {self.user_name_snapshot}'


class ClientPortalActivity(models.Model):
    """Module-level audit trail (invitations, clients, members, lifecycle)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=64, db_index=True)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_portal_activities',
    )
    actor_name_snapshot = models.CharField(max_length=255, blank=True)
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='activities',
    )
    target = models.CharField(max_length=255, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'client_portal_activity'
        ordering = ('-created_at',)
        verbose_name = 'Client portal activity'
        verbose_name_plural = 'Client portal activity'

    def __str__(self):
        return f'{self.event_type} · {self.summary}'


class TermsAcceptance(models.Model):
    """Legal proof that a user accepted the Terms and Privacy Policy.

    Captured at first access (invitation acceptance) with the digital evidence
    required by the RGPD accountability principle: IP, region, device, user
    agent, timestamp and the accepted document versions. A sealed PDF is stored
    in object storage and mirrored to the company's 10-year RGPD archive.

    Never deleted: this row and its PDF are the retention evidence, so the
    cleanup task and admin deletion must leave them untouched.
    """

    CONTEXT_INVITATION = 'invitation'
    CONTEXT_FIRST_ACCESS = 'first_access'
    CONTEXT_CHOICES = (
        (CONTEXT_INVITATION, 'Invitation acceptance'),
        (CONTEXT_FIRST_ACCESS, 'First access'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_terms_acceptances',
    )
    # Snapshots survive user anonymisation / client archival.
    email_snapshot = models.EmailField(blank=True)
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='terms_acceptances',
    )
    client_name_snapshot = models.CharField(max_length=255, blank=True)
    context = models.CharField(max_length=32, choices=CONTEXT_CHOICES, default=CONTEXT_INVITATION)

    terms_version = models.CharField(max_length=32)
    privacy_version = models.CharField(max_length=32)

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    country_code = models.CharField(max_length=8, blank=True)
    region = models.CharField(max_length=128, blank=True)
    device = models.CharField(max_length=255, blank=True)
    user_agent = models.TextField(blank=True)

    # PDF proof: key in object storage plus the mirror path in the RGPD archive.
    pdf_storage_key = models.CharField(max_length=512, blank=True)
    archived_path = models.CharField(max_length=512, blank=True)
    archived_at = models.DateTimeField(blank=True, null=True)

    accepted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'client_portal_terms_acceptance'
        ordering = ('-accepted_at',)
        verbose_name = 'Terms acceptance'
        verbose_name_plural = 'Terms acceptances'

    def __str__(self):
        return f'{self.email_snapshot} · {self.accepted_at:%Y-%m-%d}'


class DeletedDocument(Document):
    """Admin-only proxy listing recycled documents separately from the main list."""

    class Meta:
        proxy = True
        verbose_name = 'Documento eliminado'
        verbose_name_plural = 'Documentos eliminados'


class ProtocolSubject(models.Model):
    """Catalogue of request subjects a client can pick when opening a protocol.

    Each subject carries a response SLA (in hours): opening a request stamps the
    protocol with the deadline, and the client is told when to expect an answer.
    Managed in the Admin; deactivated rather than deleted so history survives.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, help_text='Shown to the client when choosing the subject.')
    # Optional mapping to the internal protocol category (for staff filtering).
    category = models.CharField(max_length=32, blank=True)
    sla_hours = models.PositiveIntegerField(default=48, help_text='Hours the office has to respond.')
    active = models.BooleanField(default=True, db_index=True)
    order = models.PositiveSmallIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_portal_protocol_subject'
        ordering = ('order', 'name')
        verbose_name = 'Protocol subject'
        verbose_name_plural = 'Protocol subjects'

    def __str__(self):
        return f'{self.name} (SLA {self.sla_hours}h)'
