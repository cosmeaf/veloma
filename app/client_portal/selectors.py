from django.db.models import Q

from .models import (
    Client,
    ClientFolder,
    ClientInvitation,
    ClientMember,
    Document,
    LifecycleStatus,
    Protocol,
    ProtocolComment,
    ProtocolEvent,
)

STAFF_GROUPS = {'STAFF', 'STAFF_MANAGER'}


def group_names(user):
    return set(user.groups.values_list('name', flat=True))


def is_manager(user):
    return bool(user and user.is_authenticated and 'STAFF_MANAGER' in group_names(user))


def is_staff_member(user):
    return bool(user and user.is_authenticated and group_names(user) & STAFF_GROUPS)


def active_membership_ids(user):
    """Client ids the user is actively linked to. Never trust a client id from the request."""
    return ClientMember.objects.filter(
        user=user,
        status=LifecycleStatus.ACTIVE,
        client__status__in=(LifecycleStatus.ACTIVE, LifecycleStatus.DEACTIVATED),
    ).values_list('client_id', flat=True)


def visible_clients(user):
    if is_manager(user):
        return Client.objects.all()
    if is_staff_member(user):
        return Client.objects.filter(Q(assigned_staff=user) | Q(assigned_staff__isnull=True))
    return Client.objects.filter(id__in=active_membership_ids(user))


def operational_clients(user):
    """Same as `visible_clients` without archived records."""
    return visible_clients(user).exclude(status=LifecycleStatus.ARCHIVED)


def visible_protocols(user):
    queryset = Protocol.objects.select_related('client', 'assigned_to', 'created_by')
    if is_manager(user):
        return queryset
    if is_staff_member(user):
        return queryset.filter(client__in=visible_clients(user))
    return queryset.filter(client_id__in=active_membership_ids(user)).exclude(status=Protocol.STATUS_DRAFT)


def visible_documents(user):
    queryset = Document.objects.select_related('client', 'protocol', 'folder', 'current_version')
    # Recycled documents never appear in the normal listings.
    queryset = queryset.exclude(status=Document.STATUS_DELETED)
    if is_staff_member(user):
        return queryset.filter(client__in=visible_clients(user))
    # A document inside an internal folder stays internal, whatever its own flag.
    return (
        queryset.filter(client_id__in=active_membership_ids(user))
        .exclude(visibility=Document.VISIBILITY_STAFF_ONLY)
        .exclude(folder__visibility=ClientFolder.VISIBILITY_STAFF_ONLY)
    )




def visible_folders(user):
    queryset = ClientFolder.objects.select_related('client', 'parent')
    if is_staff_member(user):
        return queryset.filter(client__in=visible_clients(user))
    return queryset.filter(
        client_id__in=active_membership_ids(user),
        archived_at__isnull=True,
    ).exclude(visibility=ClientFolder.VISIBILITY_STAFF_ONLY)


def visible_comments(user, protocol):
    queryset = ProtocolComment.objects.filter(protocol=protocol, archived_at__isnull=True)
    if is_staff_member(user):
        return queryset
    # Internal notes never leave the staff scope: filtered in the queryset, not the UI.
    return queryset.filter(visibility=ProtocolComment.VISIBILITY_PUBLIC)


def visible_events(user, protocol):
    queryset = ProtocolEvent.objects.filter(protocol=protocol)
    if is_staff_member(user):
        return queryset
    return queryset.filter(event_type__in=ProtocolEvent.CLIENT_VISIBLE)


def visible_invitations(user):
    queryset = ClientInvitation.objects.select_related('client', 'invited_by')
    if is_manager(user):
        return queryset
    return queryset.filter(client__in=visible_clients(user))


def visible_members(user):
    queryset = ClientMember.objects.select_related('client', 'user')
    if is_staff_member(user):
        return queryset.filter(client__in=visible_clients(user))
    return queryset.filter(client_id__in=active_membership_ids(user))


def membership_for(user, client):
    return ClientMember.objects.filter(
        user=user,
        client=client,
        status=LifecycleStatus.ACTIVE,
    ).first()
