from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny, IsAdminUser,
)

from .models import Contest, Entry, Vote, WorkflowStep
from .serializers import (
    ContestSerializer, ContestListSerializer, EntrySerializer,
    SubmissionSerializer, VoteSerializer, WorkflowStepSerializer,
)


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
    Read access is public (the archived board).
    POST is the public Step-1 submission pipeline.
    Edits/deletes are restricted to Chancellors (staff).
    """
    queryset = Entry.objects.select_related('contest').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissionSerializer
        return EntrySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
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
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        # Respond with the full board representation of the new submission.
        return Response(EntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.select_related('user', 'entry').all()
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        entry_id = self.request.query_params.get('entry')
        if entry_id:
            qs = qs.filter(entry_id=entry_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
