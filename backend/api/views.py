import os

from django.conf import settings
from django.core.mail import send_mail

from rest_framework import viewsets, status, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny, IsAdminUser,
)

from . import storage
from .models import Contest, Entry, Invitation, VoteIntention, WorkflowStep
from .serializers import (
    ContestSerializer, ContestListSerializer, EntryAdminSerializer, EntrySerializer,
    InvitationSerializer, SubmissionSerializer, VoteIntentionSerializer,
    WorkflowStepSerializer,
)

BOARD_URL = os.getenv('BOARD_URL', 'https://collegebeta.phever.dev')


def send_invitation_email(invitation):
    """Email a new noble the link to accept their Chancellor's invitation."""
    link = f"{BOARD_URL}/accept-invite?token={invitation.token}"
    greeting = invitation.in_game_name or 'noble'
    subject = "You're invited to the Mileth College Contest Hall"
    body = "\n".join([
        f"Hail {greeting},",
        "",
        "A College Chancellor has invited you to join the Mileth College Contest Hall, "
        "where qualified nobles review contest entries and prepare their recommendations.",
        "",
        "Create your account here (this link expires in two weeks):",
        link,
        "",
        "Your in-game name and email were set by the Chancellor and cannot be changed.",
        "",
        "— Mileth College Contest Hall",
    ])
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [invitation.email], fail_silently=False)


def _is_chancellor(user):
    return bool(user and user.is_authenticated and (user.is_staff or getattr(user, 'role', '') == 'admin'))


class ContestViewSet(viewsets.ModelViewSet):
    queryset = Contest.objects.all().order_by('-is_active', '-id')
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return ContestListSerializer
        return ContestSerializer


class WorkflowStepViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowStep.objects.all()
    serializer_class = WorkflowStepSerializer
    permission_classes = [AllowAny]


class EntryViewSet(viewsets.ModelViewSet):
    """
    Read access is public (the archived board). Creating/editing entries is
    restricted to Chancellors — actual contest submission happens in-game, and a
    Chancellor records it here.
    """
    queryset = Entry.objects.select_related('contest').all()
    # Search the Archive (and board) by entrant name or work title via ?search=.
    filter_backends = [filters.SearchFilter]
    search_fields = ['entrant_name', 'work_title']

    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissionSerializer
        if self.action in ('update', 'partial_update'):
            return EntryAdminSerializer
        return EntrySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = super().get_queryset()
        contest_id = self.request.query_params.get('contest')
        if contest_id:
            qs = qs.filter(contest_id=contest_id)
        subject = self.request.query_params.get('subject')
        if subject:
            qs = qs.filter(work_subject=subject)
        # archived: 'true' → Archive only, 'all' → everything, default → live board.
        archived = self.request.query_params.get('archived')
        if archived == 'true':
            qs = qs.filter(is_archived=True)
        elif archived != 'all':
            qs = qs.filter(is_archived=False)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        return Response(EntrySerializer(entry).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='advance-step',
            permission_classes=[IsAdminUser])
    def advance_step(self, request, pk=None):
        """Chancellor-only: move this entry one step forward in the workflow."""
        entry = self.get_object()
        if not entry.advance_step():
            return Response(
                {'detail': 'This entry is already at the final step (Nobility Awarded).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(EntrySerializer(entry).data)

    @action(detail=True, methods=['post'], url_path='archive-upload-url',
            permission_classes=[IsAdminUser])
    def archive_upload_url(self, request, pk=None):
        """Chancellor-only: presigned PUT URL to upload an archived copy to storage."""
        if not storage.is_configured():
            return Response({'detail': 'Archive storage is not configured.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        entry = self.get_object()
        filename = request.data.get('filename', 'file')
        content_type = request.data.get('content_type') or 'application/octet-stream'
        key = storage.safe_key(entry.id, filename)
        return Response({
            'upload_url': storage.presign_put(key, content_type),
            'public_url': storage.public_url(key),
            'content_type': content_type,
        })


class VoteIntentionViewSet(viewsets.ModelViewSet):
    """
    A noble's PRIVATE vote intention / draft review. Only the author and
    Chancellors can see it. Creating one for an entry the noble already has an
    intention on updates it (one per user per entry).
    """
    serializer_class = VoteIntentionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = VoteIntention.objects.select_related('user', 'entry')
        if not _is_chancellor(user):
            qs = qs.filter(user=user)  # nobles only ever see their own
        entry_id = self.request.query_params.get('entry')
        if entry_id:
            qs = qs.filter(entry_id=entry_id)
        return qs

    def create(self, request, *args, **kwargs):
        # Upsert: a noble has at most one intention per entry.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.validated_data['entry']
        obj, _created = VoteIntention.objects.update_or_create(
            user=request.user, entry=entry,
            defaults={
                'recommendation': serializer.validated_data.get('recommendation', ''),
                'review_text': serializer.validated_data.get('review_text', ''),
                'remind_before_close': serializer.validated_data.get('remind_before_close', False),
            },
        )
        out = self.get_serializer(obj)
        return Response(out.data, status=status.HTTP_201_CREATED if _created else status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class InvitationViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Chancellor-only: send, list, and revoke account invitations. Creating an
    invitation emails the invitee a token link to set up their account. The
    token itself is never returned by the API — only delivered by email.
    """
    queryset = Invitation.objects.select_related('invited_by').all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        invitation = serializer.save(
            invited_by=self.request.user,
            token=Invitation.generate_token(),
        )
        send_invitation_email(invitation)
