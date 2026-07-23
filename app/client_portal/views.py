from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny

import logging

from config.common.responses import api_response

from . import selectors

logger = logging.getLogger('app.client_portal.views')
from .models import (
    Client,
    ClientFolder,
    ClientInvitation,
    ClientMember,
    Document,
    LifecycleStatus,
    Protocol,
    ProtocolComment,
    ProtocolRequirement,
    ProtocolSubject,
)
from .permissions import IsPortalStaff, IsPortalUser, IsStaffManager
from .serializers import (
    ClientActionSerializer,
    ClientDetailSerializer,
    ClientListSerializer,
    ClientMemberSerializer,
    ClientMemberUpdateSerializer,
    ClientWriteSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
    DocumentMoveSerializer,
    DocumentRejectSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentVersionSerializer,
    DocumentVersionUploadSerializer,
    EventSerializer,
    FolderCreateSerializer,
    FolderMoveSerializer,
    FolderSerializer,
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    InvitationValidateSerializer,
    OpenRequestSerializer,
    ProtocolAssignSerializer,
    ProtocolCreateSerializer,
    ProtocolDetailSerializer,
    ProtocolListSerializer,
    ProtocolSubjectSerializer,
    ProtocolTransitionSerializer,
    ProtocolUpdateSerializer,
    RequirementCreateSerializer,
    RequirementSerializer,
    RequirementUpdateSerializer,
    StaffEventSerializer,
)
from .services import (
    ClientLifecycleService,
    ClientMemberService,
    ClientService,
    CommentService,
    DocumentService,
    FolderService,
    InvitationService,
    ProtocolService,
    RequirementService,
)


def error(message, code=http_status.HTTP_400_BAD_REQUEST):
    # Every business rejection is logged with its reason and the app namespace,
    # so a 400 in the access log always has a matching "why" line.
    logger.warning('rejected (%s): %s', code, message)
    return api_response(message=message, success=False, status=code)


class PortalView(GenericAPIView):
    permission_classes = [IsPortalUser]

    @property
    def user(self):
        return self.request.user

    def paginate(self, queryset, serializer_class, limit=100):
        data = serializer_class(queryset[:limit], many=True, context={'request': self.request}).data
        return list(data)


# ----------------------------------------------------------------- invitations


class InvitationListCreateView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = InvitationCreateSerializer

    def get(self, request):
        queryset = selectors.visible_invitations(request.user).order_by('-created_at')
        state = request.query_params.get('status')
        if state:
            queryset = queryset.filter(status=state)
        return api_response(data={'invitations': self.paginate(queryset, InvitationSerializer)})

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = selectors.operational_clients(request.user).filter(pk=serializer.validated_data['client']).first()
        if not client:
            return error('Client not found.', http_status.HTTP_404_NOT_FOUND)
        try:
            invitation, _token = InvitationService.create(
                client=client,
                email=serializer.validated_data['email'],
                role=serializer.validated_data['role'],
                invited_by=request.user,
                request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(
            data={'invitation': InvitationSerializer(invitation).data},
            message='Invitation sent.',
            status=http_status.HTTP_201_CREATED,
        )


class InvitationDetailView(PortalView):
    permission_classes = [IsPortalStaff]

    def get(self, request, invitation_id):
        invitation = selectors.visible_invitations(request.user).filter(pk=invitation_id).first()
        if not invitation:
            return error('Invitation not found.', http_status.HTTP_404_NOT_FOUND)
        return api_response(data={'invitation': InvitationSerializer(invitation).data})


class InvitationResendView(PortalView):
    permission_classes = [IsPortalStaff]

    def post(self, request, invitation_id):
        invitation = selectors.visible_invitations(request.user).filter(pk=invitation_id).first()
        if not invitation:
            return error('Invitation not found.', http_status.HTTP_404_NOT_FOUND)
        try:
            invitation, _token = InvitationService.resend(
                invitation=invitation, performed_by=request.user, request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(data={'invitation': InvitationSerializer(invitation).data}, message='Invitation resent.')


class InvitationRevokeView(PortalView):
    permission_classes = [IsPortalStaff]

    def post(self, request, invitation_id):
        invitation = selectors.visible_invitations(request.user).filter(pk=invitation_id).first()
        if not invitation:
            return error('Invitation not found.', http_status.HTTP_404_NOT_FOUND)
        try:
            invitation = InvitationService.revoke(
                invitation=invitation, performed_by=request.user, request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(data={'invitation': InvitationSerializer(invitation).data}, message='Invitation revoked.')


class InvitationValidateView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = InvitationValidateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invitation = InvitationService.validate_token(serializer.validated_data['token'])
        except ValueError as exc:
            return error(str(exc))
        return api_response(data={
            'valid': True,
            'email': invitation.email,
            'role': invitation.role,
            'client_name': invitation.client.legal_name,
            'expires_at': invitation.expires_at,
        })


class InvitationAcceptView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = InvitationAcceptSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = InvitationService.accept(
                token=data['token'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password'],
                phone=data['phone'],
                position=data['position'],
                request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(
            data={
                'accepted': True,
                'email': result['user'].email,
                'client_name': result['member'].client.legal_name,
            },
            message='Invitation accepted. You can now sign in.',
            status=http_status.HTTP_201_CREATED,
        )


# --------------------------------------------------------------------- clients


class ClientListCreateView(PortalView):
    serializer_class = ClientWriteSerializer

    def get(self, request):
        queryset = selectors.visible_clients(request.user).order_by('legal_name')
        if request.query_params.get('archived') != 'true':
            queryset = queryset.exclude(status=LifecycleStatus.ARCHIVED)
        return api_response(data={'clients': self.paginate(queryset, ClientListSerializer)})

    def post(self, request):
        if not selectors.is_staff_member(request.user):
            return error('Platform staff access is required.', http_status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            client = ClientService.create(
                data=serializer.validated_data, performed_by=request.user, request=request,
            )
        except Exception as exc:
            return error(str(exc))
        return api_response(
            data={'client': ClientDetailSerializer(client).data},
            message='Client created.',
            status=http_status.HTTP_201_CREATED,
        )


class ClientDetailView(PortalView):
    serializer_class = ClientWriteSerializer

    def _client(self, request, client_id):
        return selectors.visible_clients(request.user).filter(pk=client_id).first()

    def get(self, request, client_id):
        client = self._client(request, client_id)
        if not client:
            return error('Client not found.', http_status.HTTP_404_NOT_FOUND)
        return api_response(data={'client': ClientDetailSerializer(client).data})

    def patch(self, request, client_id):
        if not selectors.is_staff_member(request.user):
            return error('Platform staff access is required.', http_status.HTTP_403_FORBIDDEN)
        client = self._client(request, client_id)
        if not client:
            return error('Client not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            client = ClientService.update(
                client=client, data=serializer.validated_data, performed_by=request.user, request=request,
            )
        except Exception as exc:
            return error(str(exc))
        return api_response(data={'client': ClientDetailSerializer(client).data}, message='Client updated.')


class ClientLifecycleActionView(PortalView):
    permission_classes = [IsStaffManager]
    serializer_class = ClientActionSerializer
    operation = None

    def post(self, request, client_id):
        client = get_object_or_404(Client, pk=client_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')
        try:
            if self.operation == 'deactivate':
                client = ClientLifecycleService.deactivate(
                    client=client, performed_by=request.user, reason=reason, request=request,
                )
            elif self.operation == 'archive':
                client = ClientLifecycleService.archive(
                    client=client, performed_by=request.user, reason=reason, request=request,
                )
            elif self.operation == 'restore':
                client = ClientLifecycleService.restore(
                    client=client, performed_by=request.user, request=request,
                )
            else:
                client = ClientLifecycleService.reactivate(
                    client=client, performed_by=request.user, request=request,
                )
        except ValueError as exc:
            return error(str(exc))
        return api_response(
            data={'client': ClientDetailSerializer(client).data},
            message=f'Client {self.operation}d.',
        )


# --------------------------------------------------------------------- members


class ClientMemberListView(PortalView):
    def get(self, request, client_id):
        client = selectors.visible_clients(request.user).filter(pk=client_id).first()
        if not client:
            return error('Client not found.', http_status.HTTP_404_NOT_FOUND)
        queryset = selectors.visible_members(request.user).filter(client=client)
        return api_response(data={'members': self.paginate(queryset, ClientMemberSerializer)})


class ClientMemberDetailView(PortalView):
    serializer_class = ClientMemberUpdateSerializer

    def _member(self, request, member_id):
        return selectors.visible_members(request.user).filter(pk=member_id).first()

    def get(self, request, member_id):
        member = self._member(request, member_id)
        if not member:
            return error('Member not found.', http_status.HTTP_404_NOT_FOUND)
        return api_response(data={'member': ClientMemberSerializer(member).data})

    def patch(self, request, member_id):
        member = self._member(request, member_id)
        if not member:
            return error('Member not found.', http_status.HTTP_404_NOT_FOUND)
        if not selectors.is_staff_member(request.user):
            own = selectors.membership_for(request.user, member.client)
            if not own or not own.can_manage_members:
                return error('You cannot manage members of this client.', http_status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(member, field, value)
        member.save()
        return api_response(data={'member': ClientMemberSerializer(member).data}, message='Member updated.')


class ClientMemberActionView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = ClientActionSerializer
    operation = None

    def post(self, request, member_id):
        member = selectors.visible_members(request.user).filter(pk=member_id).first()
        if not member:
            return error('Member not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')
        try:
            if self.operation == 'deactivate':
                member = ClientMemberService.deactivate(
                    member=member, performed_by=request.user, reason=reason, request=request,
                )
            elif self.operation == 'archive':
                member = ClientMemberService.archive(
                    member=member, performed_by=request.user, reason=reason, request=request,
                )
            else:
                member = ClientMemberService.restore(
                    member=member, performed_by=request.user, request=request,
                )
        except ValueError as exc:
            return error(str(exc))
        return api_response(data={'member': ClientMemberSerializer(member).data}, message=f'Member {self.operation}d.')


# ------------------------------------------------------------------- protocols


class ProtocolListCreateView(PortalView):
    serializer_class = ProtocolCreateSerializer

    def get(self, request):
        queryset = selectors.visible_protocols(request.user)
        for field in ('status', 'category', 'client'):
            value = request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        if request.query_params.get('open') == 'true':
            queryset = queryset.exclude(
                status__in=(Protocol.STATUS_COMPLETED, Protocol.STATUS_CANCELLED, Protocol.STATUS_ARCHIVED)
            )
        return api_response(data={'protocols': self.paginate(queryset.order_by('-created_at'), ProtocolListSerializer)})

    def post(self, request):
        if not selectors.is_staff_member(request.user):
            return error('Platform staff access is required.', http_status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        client = selectors.operational_clients(request.user).filter(pk=data.pop('client')).first()
        if not client:
            return error('Client not found.', http_status.HTTP_404_NOT_FOUND)
        try:
            protocol = ProtocolService.create(
                client=client, data=data, created_by=request.user, request=request,
            )
        except (ValueError, Exception) as exc:
            return error(str(exc))
        return api_response(
            data={'protocol': ProtocolDetailSerializer(protocol, context={'request': request}).data},
            message='Protocol created.',
            status=http_status.HTTP_201_CREATED,
        )


class SubjectListView(PortalView):
    """Active request subjects the client can choose from (with their SLA)."""

    serializer_class = ProtocolSubjectSerializer

    def get(self, request):
        subjects = ProtocolSubject.objects.filter(active=True).order_by('order', 'name')
        return api_response(data={'subjects': ProtocolSubjectSerializer(subjects, many=True).data})


class RequestOpenView(PortalView):
    """Client self-service: opens a protocol for a chosen subject."""

    serializer_class = OpenRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subject = ProtocolSubject.objects.filter(pk=data['subject'], active=True).first()
        if not subject:
            return error('Assunto indisponível.', http_status.HTTP_404_NOT_FOUND)

        clients = selectors.operational_clients(request.user)
        if data.get('client'):
            client = clients.filter(pk=data['client']).first()
        else:
            client = clients.first()
        if not client:
            return error('Cliente não encontrado.', http_status.HTTP_404_NOT_FOUND)

        try:
            protocol = ProtocolService.open_request(
                client=client,
                subject=subject,
                title=data.get('title', ''),
                description=data.get('description', ''),
                created_by=request.user,
                request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(
            data={'protocol': ProtocolDetailSerializer(protocol, context={'request': request}).data},
            message='Pedido aberto.',
            status=http_status.HTTP_201_CREATED,
        )


class ProtocolDetailView(PortalView):
    serializer_class = ProtocolUpdateSerializer

    def _protocol(self, request, protocol_id):
        return selectors.visible_protocols(request.user).filter(pk=protocol_id).first()

    def get(self, request, protocol_id):
        protocol = self._protocol(request, protocol_id)
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        return api_response(data={
            'protocol': ProtocolDetailSerializer(protocol, context={'request': request}).data,
        })

    def patch(self, request, protocol_id):
        if not selectors.is_staff_member(request.user):
            return error('Platform staff access is required.', http_status.HTTP_403_FORBIDDEN)
        protocol = self._protocol(request, protocol_id)
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        protocol = ProtocolService.update(
            protocol=protocol, data=serializer.validated_data, performed_by=request.user, request=request,
        )
        return api_response(data={
            'protocol': ProtocolDetailSerializer(protocol, context={'request': request}).data,
        }, message='Protocol updated.')


class ProtocolTransitionView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = ProtocolTransitionSerializer
    target_status = None

    def post(self, request, protocol_id):
        protocol = selectors.visible_protocols(request.user).filter(pk=protocol_id).first()
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        if self.target_status:
            target = self.target_status
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            target = serializer.validated_data['status']
        try:
            protocol = ProtocolService.transition(
                protocol=protocol,
                status=target,
                performed_by=request.user,
                is_manager=selectors.is_manager(request.user),
                request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(data={
            'protocol': ProtocolDetailSerializer(protocol, context={'request': request}).data,
        }, message='Protocol updated.')


class ProtocolAssignView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = ProtocolAssignSerializer

    def post(self, request, protocol_id):
        protocol = selectors.visible_protocols(request.user).filter(pk=protocol_id).first()
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff_user = User.objects.filter(pk=serializer.validated_data['assigned_to'], is_active=True).first()
        if not staff_user or not selectors.is_staff_member(staff_user):
            return error('The selected user is not platform staff.')
        protocol = ProtocolService.assign(
            protocol=protocol, staff_user=staff_user, performed_by=request.user, request=request,
        )
        return api_response(data={
            'protocol': ProtocolDetailSerializer(protocol, context={'request': request}).data,
        }, message='Protocol assigned.')


class ProtocolTimelineView(PortalView):
    def get(self, request, protocol_id):
        protocol = selectors.visible_protocols(request.user).filter(pk=protocol_id).first()
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        events = selectors.visible_events(request.user, protocol).order_by('-created_at')
        serializer_class = StaffEventSerializer if selectors.is_staff_member(request.user) else EventSerializer
        return api_response(data={'timeline': self.paginate(events, serializer_class, limit=200)})


# ---------------------------------------------------------------- requirements


class RequirementListCreateView(PortalView):
    serializer_class = RequirementCreateSerializer

    def get(self, request, protocol_id):
        protocol = selectors.visible_protocols(request.user).filter(pk=protocol_id).first()
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        queryset = protocol.requirements.order_by('created_at')
        return api_response(data={'requirements': self.paginate(queryset, RequirementSerializer)})

    def post(self, request, protocol_id):
        if not selectors.is_staff_member(request.user):
            return error('Platform staff access is required.', http_status.HTTP_403_FORBIDDEN)
        protocol = selectors.visible_protocols(request.user).filter(pk=protocol_id).first()
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requirement = RequirementService.create(
            protocol=protocol, data=serializer.validated_data, created_by=request.user, request=request,
        )
        return api_response(
            data={'requirement': RequirementSerializer(requirement).data},
            message='Document requested.',
            status=http_status.HTTP_201_CREATED,
        )


class RequirementDetailView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = RequirementUpdateSerializer

    def patch(self, request, requirement_id):
        requirement = ProtocolRequirement.objects.filter(pk=requirement_id).first()
        if not requirement or not selectors.visible_protocols(request.user).filter(pk=requirement.protocol_id).exists():
            return error('Requirement not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requirement = RequirementService.update_status(
            requirement=requirement,
            status=serializer.validated_data['status'],
            performed_by=request.user,
            request=request,
        )
        return api_response(data={'requirement': RequirementSerializer(requirement).data}, message='Requirement updated.')


# -------------------------------------------------------------------- comments


class CommentListCreateView(PortalView):
    serializer_class = CommentCreateSerializer

    def get(self, request, protocol_id):
        protocol = selectors.visible_protocols(request.user).filter(pk=protocol_id).first()
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        queryset = selectors.visible_comments(request.user, protocol).order_by('created_at')
        return api_response(data={'comments': self.paginate(queryset, CommentSerializer, limit=300)})

    def post(self, request, protocol_id):
        protocol = selectors.visible_protocols(request.user).filter(pk=protocol_id).first()
        if not protocol:
            return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visibility = serializer.validated_data['visibility']
        if visibility == ProtocolComment.VISIBILITY_INTERNAL and not selectors.is_staff_member(request.user):
            return error('Only staff can add internal notes.', http_status.HTTP_403_FORBIDDEN)
        if not selectors.is_staff_member(request.user):
            membership = selectors.membership_for(request.user, protocol.client)
            if not membership or not membership.can_comment:
                return error('You cannot comment on this protocol.', http_status.HTTP_403_FORBIDDEN)
        comment = CommentService.create(
            protocol=protocol,
            author=request.user,
            message=serializer.validated_data['message'],
            visibility=visibility,
            request=request,
        )
        return api_response(
            data={'comment': CommentSerializer(comment).data},
            message='Comment added.',
            status=http_status.HTTP_201_CREATED,
        )


class CommentDetailView(PortalView):
    serializer_class = CommentUpdateSerializer

    def _comment(self, request, comment_id):
        comment = ProtocolComment.objects.filter(pk=comment_id).first()
        if not comment:
            return None
        if not selectors.visible_protocols(request.user).filter(pk=comment.protocol_id).exists():
            return None
        if comment.visibility == ProtocolComment.VISIBILITY_INTERNAL and not selectors.is_staff_member(request.user):
            return None
        return comment

    def patch(self, request, comment_id):
        comment = self._comment(request, comment_id)
        if not comment:
            return error('Comment not found.', http_status.HTTP_404_NOT_FOUND)
        if comment.author_id != request.user.id:
            return error('Only the author can edit this comment.', http_status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = CommentService.update(comment=comment, message=serializer.validated_data['message'])
        return api_response(data={'comment': CommentSerializer(comment).data}, message='Comment updated.')


class CommentArchiveView(PortalView):
    permission_classes = [IsPortalStaff]

    def post(self, request, comment_id):
        comment = ProtocolComment.objects.filter(pk=comment_id).first()
        if not comment or not selectors.visible_protocols(request.user).filter(pk=comment.protocol_id).exists():
            return error('Comment not found.', http_status.HTTP_404_NOT_FOUND)
        comment = CommentService.archive(comment=comment)
        return api_response(data={'comment': CommentSerializer(comment).data}, message='Comment archived.')


# --------------------------------------------------------------------- folders


class FolderListCreateView(PortalView):
    serializer_class = FolderCreateSerializer

    def get(self, request):
        queryset = selectors.visible_folders(request.user)
        client_id = request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        parent = request.query_params.get('parent')
        if parent == 'root':
            queryset = queryset.filter(parent__isnull=True)
        elif parent:
            queryset = queryset.filter(parent_id=parent)
        return api_response(data={'folders': self.paginate(queryset.order_by('name'), FolderSerializer, limit=300)})

    def post(self, request):
        if not selectors.is_staff_member(request.user):
            return error('Platform staff access is required.', http_status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        client = selectors.operational_clients(request.user).filter(pk=data['client']).first()
        if not client:
            return error('Client not found.', http_status.HTTP_404_NOT_FOUND)
        parent = ClientFolder.objects.filter(pk=data.get('parent'), client=client).first() if data.get('parent') else None
        protocol = Protocol.objects.filter(pk=data.get('protocol'), client=client).first() if data.get('protocol') else None
        try:
            folder = FolderService.create(
                client=client, name=data['name'], parent=parent, protocol=protocol,
                visibility=data['visibility'], created_by=request.user, request=request,
            )
        except Exception as exc:
            return error(str(exc))
        return api_response(
            data={'folder': FolderSerializer(folder).data},
            message='Folder created.',
            status=http_status.HTTP_201_CREATED,
        )


class FolderDetailView(PortalView):
    serializer_class = FolderSerializer

    def get(self, request, folder_id):
        folder = selectors.visible_folders(request.user).filter(pk=folder_id).first()
        if not folder:
            return error('Folder not found.', http_status.HTTP_404_NOT_FOUND)
        children = selectors.visible_folders(request.user).filter(parent=folder).order_by('name')
        documents = selectors.visible_documents(request.user).filter(folder=folder).order_by('-created_at')
        return api_response(data={
            'folder': FolderSerializer(folder).data,
            'children': FolderSerializer(children[:300], many=True).data,
            'documents': DocumentSerializer(documents[:300], many=True).data,
        })

    def patch(self, request, folder_id):
        if not selectors.is_staff_member(request.user):
            return error('Platform staff access is required.', http_status.HTTP_403_FORBIDDEN)
        folder = selectors.visible_folders(request.user).filter(pk=folder_id).first()
        if not folder:
            return error('Folder not found.', http_status.HTTP_404_NOT_FOUND)
        name = request.data.get('name')
        if name:
            folder.name = name.strip()[:180]
            folder.save(update_fields=('name', 'updated_at'))
        return api_response(data={'folder': FolderSerializer(folder).data}, message='Folder updated.')


class FolderMoveView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = FolderMoveSerializer

    def post(self, request, folder_id):
        folder = selectors.visible_folders(request.user).filter(pk=folder_id).first()
        if not folder:
            return error('Folder not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent_id = serializer.validated_data.get('parent')
        parent = ClientFolder.objects.filter(pk=parent_id).first() if parent_id else None
        try:
            folder = FolderService.move(folder=folder, parent=parent, performed_by=request.user)
        except Exception as exc:
            return error(str(exc))
        return api_response(data={'folder': FolderSerializer(folder).data}, message='Folder moved.')


class FolderArchiveView(PortalView):
    permission_classes = [IsPortalStaff]

    def post(self, request, folder_id):
        folder = selectors.visible_folders(request.user).filter(pk=folder_id).first()
        if not folder:
            return error('Folder not found.', http_status.HTTP_404_NOT_FOUND)
        folder = FolderService.archive(folder=folder, performed_by=request.user)
        return api_response(data={'folder': FolderSerializer(folder).data}, message='Folder archived.')


# ------------------------------------------------------------------- documents


class DocumentListView(PortalView):
    def get(self, request):
        queryset = selectors.visible_documents(request.user)
        for field in ('client', 'protocol', 'folder', 'status'):
            value = request.query_params.get(field)
            if not value:
                continue
            # `none` lists what sits outside the folder tree, for the explorer root.
            if value == 'none':
                queryset = queryset.filter(**{f'{field}__isnull': True})
            else:
                queryset = queryset.filter(**{field: value})
        return api_response(data={'documents': self.paginate(queryset.order_by('-created_at'), DocumentSerializer)})


class DocumentUploadView(PortalView):
    serializer_class = DocumentUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        protocol = None
        if data.get('protocol'):
            protocol = selectors.visible_protocols(request.user).filter(pk=data['protocol']).first()
            if not protocol:
                return error('Protocol not found.', http_status.HTTP_404_NOT_FOUND)
            client = protocol.client
        elif data.get('client'):
            client = selectors.operational_clients(request.user).filter(pk=data['client']).first()
            if not client:
                return error('Client not found.', http_status.HTTP_404_NOT_FOUND)
        else:
            return error('Provide a client or a protocol.')

        if not selectors.is_staff_member(request.user):
            membership = selectors.membership_for(request.user, client)
            if not membership or not membership.can_upload:
                return error('You cannot upload documents for this client.', http_status.HTTP_403_FORBIDDEN)
            if data['visibility'] == Document.VISIBILITY_STAFF_ONLY:
                return error('You cannot create staff-only documents.', http_status.HTTP_403_FORBIDDEN)

        folder = ClientFolder.objects.filter(pk=data.get('folder'), client=client).first() if data.get('folder') else None
        requirement = None
        if data.get('requirement') and protocol is not None:
            requirement = ProtocolRequirement.objects.filter(pk=data['requirement'], protocol=protocol).first()

        try:
            document, version = DocumentService.upload(
                client=client,
                upload=data['file'],
                title=data['title'],
                protocol=protocol,
                folder=folder,
                requirement=requirement,
                visibility=data['visibility'],
                uploaded_by=request.user,
                is_staff=selectors.is_staff_member(request.user),
                request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(
            data={
                'document': DocumentSerializer(document).data,
                'version': DocumentVersionSerializer(version).data,
            },
            message='Upload received. The file becomes available after the scan.',
            status=http_status.HTTP_201_CREATED,
        )


class DocumentDetailView(PortalView):
    def get(self, request, document_id):
        document = selectors.visible_documents(request.user).filter(pk=document_id).first()
        if not document:
            return error('Document not found.', http_status.HTTP_404_NOT_FOUND)
        return api_response(data={'document': DocumentSerializer(document).data})


class DocumentVersionListView(PortalView):
    def get(self, request, document_id):
        document = selectors.visible_documents(request.user).filter(pk=document_id).first()
        if not document:
            return error('Document not found.', http_status.HTTP_404_NOT_FOUND)
        versions = document.versions.order_by('-version_number')
        return api_response(data={'versions': DocumentVersionSerializer(versions, many=True).data})


class DocumentNewVersionView(PortalView):
    serializer_class = DocumentVersionUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, document_id):
        document = selectors.visible_documents(request.user).filter(pk=document_id).first()
        if not document:
            return error('Document not found.', http_status.HTTP_404_NOT_FOUND)
        if not selectors.is_staff_member(request.user):
            membership = selectors.membership_for(request.user, document.client)
            if not membership or not membership.can_upload:
                return error('You cannot upload documents for this client.', http_status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            version = DocumentService.new_version(
                document=document,
                upload=serializer.validated_data['file'],
                uploaded_by=request.user,
                change_reason=serializer.validated_data['change_reason'],
                is_staff=selectors.is_staff_member(request.user),
                request=request,
            )
        except ValueError as exc:
            return error(str(exc))
        return api_response(
            data={'version': DocumentVersionSerializer(version).data},
            message='New version stored.',
            status=http_status.HTTP_201_CREATED,
        )


class DocumentDownloadView(PortalView):
    def post(self, request, document_id):
        document = selectors.visible_documents(request.user).filter(pk=document_id).first()
        if not document:
            return error('Document not found.', http_status.HTTP_404_NOT_FOUND)
        if not selectors.is_staff_member(request.user):
            membership = selectors.membership_for(request.user, document.client)
            if not membership or not membership.can_download:
                return error('You cannot download documents for this client.', http_status.HTTP_403_FORBIDDEN)
        try:
            payload = DocumentService.build_download(document=document, user=request.user, request=request)
        except ValueError as exc:
            return error(str(exc))
        return api_response(data=payload, message='Signed URL created.')


class DocumentMoveView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = DocumentMoveSerializer

    def post(self, request, document_id):
        document = selectors.visible_documents(request.user).filter(pk=document_id).first()
        if not document:
            return error('Document not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        folder_id = serializer.validated_data.get('folder')
        folder = ClientFolder.objects.filter(pk=folder_id).first() if folder_id else None
        try:
            document = DocumentService.move(document=document, folder=folder, performed_by=request.user)
        except ValueError as exc:
            return error(str(exc))
        return api_response(data={'document': DocumentSerializer(document).data}, message='Document moved.')


class DocumentRejectView(PortalView):
    permission_classes = [IsPortalStaff]
    serializer_class = DocumentRejectSerializer

    def post(self, request, document_id):
        document = selectors.visible_documents(request.user).filter(pk=document_id).first()
        if not document:
            return error('Document not found.', http_status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = DocumentService.reject(
            document=document,
            reason=serializer.validated_data['reason'],
            performed_by=request.user,
            request=request,
        )
        return api_response(data={'document': DocumentSerializer(document).data}, message='Document rejected.')


class DocumentArchiveView(PortalView):
    permission_classes = [IsPortalStaff]

    def post(self, request, document_id):
        document = selectors.visible_documents(request.user).filter(pk=document_id).first()
        if not document:
            return error('Document not found.', http_status.HTTP_404_NOT_FOUND)
        document = DocumentService.archive(document=document, performed_by=request.user, request=request)
        return api_response(data={'document': DocumentSerializer(document).data}, message='Document archived.')


# ------------------------------------------------------------------ dashboards


class DashboardView(PortalView):
    """Aggregated counters for the staff and client dashboards."""

    def get(self, request):
        protocols = selectors.visible_protocols(request.user)
        documents = selectors.visible_documents(request.user)
        data = {
            'protocols': {
                'waiting_documents': protocols.filter(status=Protocol.STATUS_WAITING_DOCUMENTS).count(),
                'documents_received': protocols.filter(status=Protocol.STATUS_DOCUMENTS_RECEIVED).count(),
                'under_review': protocols.filter(status=Protocol.STATUS_UNDER_REVIEW).count(),
                'action_required': protocols.filter(status=Protocol.STATUS_ACTION_REQUIRED).count(),
                'processing': protocols.filter(status=Protocol.STATUS_PROCESSING).count(),
                'completed': protocols.filter(status=Protocol.STATUS_COMPLETED).count(),
            },
            'recent_protocols': ProtocolListSerializer(
                protocols.order_by('-updated_at')[:10], many=True, context={'request': request},
            ).data,
        }
        if selectors.is_staff_member(request.user):
            from django.utils import timezone

            data['staff'] = {
                'overdue': protocols.filter(
                    due_date__lt=timezone.now().date(),
                ).exclude(
                    status__in=(Protocol.STATUS_COMPLETED, Protocol.STATUS_CANCELLED, Protocol.STATUS_ARCHIVED),
                ).count(),
                'pending_scan': documents.filter(status=Document.STATUS_PENDING_SCAN).count(),
                'quarantined': documents.filter(
                    status__in=(Document.STATUS_QUARANTINED, Document.STATUS_INFECTED),
                ).count(),
                'pending_invitations': selectors.visible_invitations(request.user).filter(
                    status=ClientInvitation.STATUS_PENDING,
                ).count(),
                'expired_invitations': selectors.visible_invitations(request.user).filter(
                    status=ClientInvitation.STATUS_EXPIRED,
                ).count(),
                'clients': selectors.operational_clients(request.user).count(),
            }
        else:
            data['requirements_pending'] = ProtocolRequirement.objects.filter(
                protocol__in=protocols, status=ProtocolRequirement.STATUS_PENDING,
            ).count()
        return api_response(data=data)
