"""Builds a notification feed from activity already recorded.

Staff see the movement of their clients (uploads, accepted invitations, new
protocols); clients see the progress of their own protocols. No dedicated table
— the feed is derived, and "read" state is a single timestamp per user.
"""


def _staff_groups(user):
    return set(user.groups.values_list('name', flat=True))


def build_notifications(user, *, limit=20, since=None):
    """Feed of recent activity. ``since`` (the user's cleared_at) hides anything
    the user has cleared, so "apagar tudo" empties the list."""
    from app.client_portal.models import ClientPortalActivity, ProtocolEvent
    from app.client_portal.selectors import is_staff_member, visible_clients, visible_protocols

    items = []

    if is_staff_member(user):
        clients = visible_clients(user)
        activities = ClientPortalActivity.objects.filter(client__in=clients).exclude(actor=user)
        if since is not None:
            activities = activities.filter(created_at__gt=since)
        activities = activities.order_by('-created_at')[:limit]
        for activity in activities:
            items.append({
                'id': str(activity.id),
                'title': _staff_title(activity.event_type),
                'body': activity.summary or activity.target,
                'url': f'/staff/clientes/{activity.client_id}' if activity.client_id else '/staff',
                'created_at': activity.created_at,
            })
    else:
        protocols = visible_protocols(user)
        events = ProtocolEvent.objects.filter(
            protocol__in=protocols,
            event_type__in=ProtocolEvent.CLIENT_VISIBLE,
        ).exclude(actor=user)
        if since is not None:
            events = events.filter(created_at__gt=since)
        events = events.select_related('protocol').order_by('-created_at')[:limit]
        for event in events:
            items.append({
                'id': str(event.id),
                'title': _client_title(event.event_type),
                'body': f'{event.protocol.number} · {event.protocol.title}',
                'url': f'/dashboard/protocolos/{event.protocol_id}',
                'created_at': event.created_at,
            })

    items.sort(key=lambda item: item['created_at'], reverse=True)
    return items[:limit]


_STAFF = {
    'invitation_accepted': 'Convite aceite',
    'invitation_created': 'Convite enviado',
    'document_uploaded': 'Documento enviado pelo cliente',
    'client_created': 'Cliente criado',
    'protocol_created': 'Protocolo criado',
}

_CLIENT = {
    'protocol_created': 'Novo pedido',
    'status_changed': 'Estado atualizado',
    'document_requested': 'Documentos solicitados',
    'document_uploaded': 'Documento disponível',
    'comment_added': 'Nova mensagem',
    'protocol_completed': 'Pedido concluído',
    'protocol_reopened': 'Pedido reaberto',
    'due_date_changed': 'Prazo alterado',
}


def _staff_title(event_type):
    return _STAFF.get(event_type, event_type.replace('_', ' ').capitalize())


def _client_title(event_type):
    return _CLIENT.get(event_type, event_type.replace('_', ' ').capitalize())
