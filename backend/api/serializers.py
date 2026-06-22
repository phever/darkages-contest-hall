from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from .models import Invitation, User, Contest, Entry, VoteIntention, WorkflowStep


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_verified', 'in_game_name']
        # email and in_game_name are set by Chancellors (on invite / in admin) and
        # are read-only to nobles. role/is_verified are likewise never self-set.
        read_only_fields = ['username', 'email', 'role', 'is_verified', 'in_game_name']


class WorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ['id', 'number', 'title', 'description']


class EntrySerializer(serializers.ModelSerializer):
    on_step = serializers.CharField(read_only=True)
    progress_text = serializers.CharField(read_only=True)
    steps_complete = serializers.IntegerField(source='current_step', read_only=True)
    total_steps = serializers.IntegerField(source='TOTAL_STEPS', read_only=True)

    class Meta:
        model = Entry
        fields = [
            'id', 'contest', 'entrant_name', 'work_title', 'work_subject', 'content',
            'original_location_url', 'original_location_label', 'archived_location_url',
            'review_overseer', 'review_opened', 'review_closed', 'review_closes_at',
            'recommendation', 'current_step', 'step_status', 'on_step', 'progress_text',
            'steps_complete', 'total_steps', 'is_archived', 'submitted_at',
        ]
        # These are managed by Chancellors through the admin / workflow, not by submitters.
        read_only_fields = [
            'review_overseer', 'review_opened', 'review_closed', 'review_closes_at',
            'recommendation', 'current_step', 'step_status', 'is_archived', 'submitted_at',
        ]


class EntryAdminSerializer(EntrySerializer):
    """
    Full read/write serializer for Chancellor inline edits (PUT/PATCH from the
    board). Unlike EntrySerializer — used for public reads, where the review and
    workflow fields are read-only — this lets a Chancellor edit any entry field
    without opening the Django admin. The viewset gates it to Chancellors.
    """
    class Meta(EntrySerializer.Meta):
        # The computed fields (on_step, steps_complete, …) stay read-only via
        # their field-level declarations on EntrySerializer.
        read_only_fields = ['submitted_at']


class SubmissionSerializer(serializers.ModelSerializer):
    """Chancellor-facing create serializer for board entries and archive works."""
    class Meta:
        model = Entry
        fields = [
            'id', 'contest', 'entrant_name', 'work_title', 'work_subject', 'content',
            'original_location_url', 'original_location_label', 'archived_location_url',
            'is_archived',
        ]

    def create(self, validated_data):
        # Archived works are historical; live submissions enter at Step 1.
        if validated_data.get('is_archived'):
            validated_data['current_step'] = Entry.TOTAL_STEPS
            validated_data['step_status'] = 'Archived'
        else:
            validated_data['current_step'] = 1
            validated_data['step_status'] = 'Submission'
        return super().create(validated_data)


class ContestSerializer(serializers.ModelSerializer):
    entries = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    entry_count = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            'id', 'title', 'description', 'info_message', 'start_date', 'end_date',
            'is_active', 'entry_count', 'entries', 'steps',
        ]

    def get_entries(self, obj):
        # The live board shows only non-archived works (archives live in /archive).
        qs = obj.entries.filter(is_archived=False)
        return EntrySerializer(qs, many=True).data

    def get_entry_count(self, obj):
        return obj.entries.filter(is_archived=False).count()

    def get_steps(self, obj):
        return WorkflowStepSerializer(WorkflowStep.objects.all(), many=True).data


class ContestListSerializer(serializers.ModelSerializer):
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)

    class Meta:
        model = Contest
        fields = ['id', 'title', 'description', 'info_message', 'is_active', 'entry_count']


class VoteIntentionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = VoteIntention
        fields = [
            'id', 'user', 'username', 'entry', 'recommendation', 'review_text',
            'remind_before_close', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class InvitationSerializer(serializers.ModelSerializer):
    """Chancellor-facing serializer for sending/listing invitations.

    The secret token is never exposed here — it only travels to the invitee by
    email. The Chancellor supplies the email and in-game name.
    """
    invited_by = serializers.CharField(source='invited_by.username', read_only=True, default=None)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'in_game_name', 'invited_by', 'created_at',
            'expires_at', 'accepted_at', 'status',
        ]
        read_only_fields = ['invited_by', 'created_at', 'expires_at', 'accepted_at', 'status']

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with that email already exists.')
        if Invitation.objects.filter(email__iexact=value, accepted_at__isnull=True).exists():
            raise serializers.ValidationError('A pending invitation for that email already exists.')
        return value


class AcceptInvitationSerializer(serializers.Serializer):
    """Public: a noble redeems an invitation token, choosing a username/password.

    The email and in-game name come from the invitation (Chancellor-set) and are
    intentionally not accepted here.
    """
    token = serializers.CharField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A username is required.')
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('That username is already taken.')
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
