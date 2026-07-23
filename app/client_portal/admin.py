from django.contrib import messages
from django.contrib.admin import ModelAdmin, SimpleListFilter, StackedInline, TabularInline, action, register

from config.admin import veloma_admin_site

from .models import (
    Client,
    ClientFolder,
    ClientInvitation,
    ClientMember,
    Document,
    DocumentVersion,
    LifecycleStatus,
    Protocol,
    ProtocolComment,
    ProtocolEvent,
    ProtocolRequirement,
    ProtocolSubject,
    TermsAcceptance,
)
from .services import ClientLifecycleService, DocumentService


class ReadOnlyInline(TabularInline):
    extra = 0
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)


class ArchivedFilter(SimpleListFilter):
    title = 'Archive'
    parameter_name = 'archived'

    def lookups(self, request, model_admin):
        return (('true', 'Archived'), ('false', 'Not archived'))

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(status=LifecycleStatus.ARCHIVED)
        if self.value() == 'false':
            return queryset.exclude(status=LifecycleStatus.ARCHIVED)
        return queryset


class ClientMemberInline(TabularInline):
    model = ClientMember
    extra = 0
    fields = ('user', 'role', 'position', 'status', 'can_upload', 'can_download', 'can_manage_members')
    readonly_fields = ('status',)
    can_delete = False


class ClientInvitationInline(ReadOnlyInline):
    model = ClientInvitation
    fields = ('email', 'role', 'status', 'expires_at', 'accepted_at', 'invited_by')
    exclude = ('token_hash',)

    def get_readonly_fields(self, request, obj=None):
        return self.fields


@register(Client, site=veloma_admin_site)
class ClientAdmin(ModelAdmin):
    list_display = ('legal_name', 'nif', 'entity_type', 'status', 'assigned_staff', 'created_at')
    list_filter = ('status', 'entity_type', ArchivedFilter, 'created_at')
    search_fields = ('legal_name', 'commercial_name', 'nif', 'email')
    readonly_fields = (
        'id', 'status', 'deactivated_at', 'deactivated_by', 'archived_at',
        'archived_by', 'restored_at', 'created_at', 'updated_at',
    )
    inlines = (ClientMemberInline, ClientInvitationInline)
    actions = ('deactivate_clients', 'archive_clients', 'restore_clients', 'reactivate_clients')

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def has_delete_permission(self, request, obj=None):
        return False

    def _run(self, request, queryset, operation, **kwargs):
        done, failures = 0, []
        for client in queryset:
            try:
                operation(client=client, performed_by=request.user, request=request, **kwargs)
                done += 1
            except ValueError as exc:
                failures.append(f'{client.legal_name}: {exc}')
        if done:
            self.message_user(request, f'{done} client(s) processed.')
        for failure in failures:
            self.message_user(request, failure, level=messages.WARNING)

    @action(description='Desativar clientes selecionados')
    def deactivate_clients(self, request, queryset):
        self._run(request, queryset, ClientLifecycleService.deactivate, reason='Deactivated from the Django Admin.')

    @action(description='Excluir e arquivar clientes selecionados')
    def archive_clients(self, request, queryset):
        self._run(request, queryset, ClientLifecycleService.archive, reason='Archived from the Django Admin.')

    @action(description='Restaurar clientes arquivados')
    def restore_clients(self, request, queryset):
        self._run(request, queryset, ClientLifecycleService.restore)

    @action(description='Reativar clientes selecionados')
    def reactivate_clients(self, request, queryset):
        self._run(request, queryset, ClientLifecycleService.reactivate)


@register(ClientMember, site=veloma_admin_site)
class ClientMemberAdmin(ModelAdmin):
    list_display = ('user', 'client', 'role', 'status', 'can_upload', 'can_download', 'joined_at')
    list_filter = ('status', 'role', 'client')
    search_fields = ('user__email', 'user__username', 'client__legal_name', 'client__nif')
    readonly_fields = ('id', 'status', 'joined_at', 'deactivated_at', 'archived_at', 'created_at', 'updated_at')

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


@register(ClientInvitation, site=veloma_admin_site)
class ClientInvitationAdmin(ModelAdmin):
    list_display = ('email', 'client', 'role', 'status', 'expires_at', 'resend_count', 'created_at')
    list_filter = ('status', 'role', 'created_at')
    search_fields = ('email', 'client__legal_name', 'client__nif')
    exclude = ('token_hash',)
    readonly_fields = (
        'id', 'status', 'invited_by', 'accepted_by', 'accepted_at', 'revoked_at',
        'resend_count', 'last_sent_at', 'accepted_ip', 'accepted_user_agent', 'created_at', 'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RequirementInline(TabularInline):
    model = ProtocolRequirement
    extra = 0
    fields = ('title', 'category', 'required', 'due_date', 'status')
    can_delete = False


class ProtocolCommentInline(StackedInline):
    model = ProtocolComment
    extra = 0
    fields = ('author_name_snapshot', 'message', 'visibility', 'created_at')
    readonly_fields = ('author_name_snapshot', 'created_at')
    can_delete = False


class ProtocolEventInline(ReadOnlyInline):
    model = ProtocolEvent
    fields = ('created_at', 'event_type', 'actor_name_snapshot', 'old_value', 'new_value')


@register(Protocol, site=veloma_admin_site)
class ProtocolAdmin(ModelAdmin):
    list_display = ('number', 'client', 'title', 'category', 'status', 'priority', 'assigned_to', 'due_date')
    list_filter = ('status', 'category', 'priority', 'client', 'assigned_to', 'due_date')
    search_fields = ('number', 'title', 'client__legal_name', 'client__nif')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'id', 'number', 'created_by', 'started_at', 'completed_at', 'closed_at',
        'cancelled_at', 'archived_at', 'created_at', 'updated_at',
    )
    inlines = (RequirementInline, ProtocolCommentInline, ProtocolEventInline)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


class DocumentVersionInline(ReadOnlyInline):
    model = DocumentVersion
    fk_name = 'document'
    fields = (
        'version_number', 'original_name', 'size', 'detected_mime_type',
        'checksum_sha256', 'scan_status', 'scan_message', 'created_at',
    )


@register(Document, site=veloma_admin_site)
class DocumentAdmin(ModelAdmin):
    list_display = ('title', 'client', 'protocol', 'status', 'visibility', 'uploader_name_snapshot', 'created_at')
    list_filter = ('status', 'visibility', 'client', 'created_at')
    search_fields = ('title', 'original_name', 'client__legal_name', 'client__nif')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'id', 'client', 'protocol', 'original_name', 'current_version', 'status',
        'uploaded_by', 'uploader_name_snapshot', 'uploader_email_snapshot',
        'archived_at', 'created_at', 'updated_at',
    )
    inlines = (DocumentVersionInline,)
    actions = ('rescan_documents', 'archive_documents')

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @action(description='Reexecutar análise antivírus')
    def rescan_documents(self, request, queryset):
        count = 0
        for document in queryset.exclude(current_version__isnull=True):
            DocumentService.schedule_scan(document.current_version)
            count += 1
        self.message_user(request, f'{count} document(s) queued for scanning.')

    @action(description='Arquivar documentos selecionados')
    def archive_documents(self, request, queryset):
        count = 0
        for document in queryset.filter(archived_at__isnull=True):
            DocumentService.archive(document=document, performed_by=request.user, request=request)
            count += 1
        self.message_user(request, f'{count} document(s) archived.')


@register(ClientFolder, site=veloma_admin_site)
class ClientFolderAdmin(ModelAdmin):
    list_display = ('name', 'client', 'folder_type', 'year', 'month', 'archived_at')
    list_filter = ('folder_type', 'client', 'year')
    search_fields = ('name', 'client__legal_name')
    readonly_fields = ('id', 'slug', 'created_by', 'archived_at', 'created_at', 'updated_at')

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


@register(ProtocolSubject, site=veloma_admin_site)
class ProtocolSubjectAdmin(ModelAdmin):
    """Catalogue of request subjects and their response SLA. Deactivate, never delete."""

    list_display = ('name', 'sla_hours', 'category', 'active', 'order')
    list_filter = ('active', 'category')
    list_editable = ('sla_hours', 'active', 'order')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


@register(TermsAcceptance, site=veloma_admin_site)
class TermsAcceptanceAdmin(ModelAdmin):
    """Legal consent evidence — read-only, never deletable (10-year retention)."""

    list_display = ('email_snapshot', 'client_name_snapshot', 'context', 'country_code', 'accepted_at', 'archived_at')
    list_filter = ('context', 'terms_version', 'accepted_at')
    search_fields = ('email_snapshot', 'client_name_snapshot', 'ip_address')
    date_hierarchy = 'accepted_at'
    readonly_fields = (
        'id', 'user', 'email_snapshot', 'client', 'client_name_snapshot', 'context',
        'terms_version', 'privacy_version', 'ip_address', 'country_code', 'region',
        'device', 'user_agent', 'pdf_storage_key', 'archived_path', 'archived_at', 'accepted_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def has_delete_permission(self, request, obj=None):
        return False
