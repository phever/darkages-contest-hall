from rest_framework import serializers
from .models import User, Contest, Entry, VoteIntention, WorkflowStep


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_verified', 'in_game_name']


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
            'steps_complete', 'total_steps', 'submitted_at',
        ]
        # These are managed by Chancellors through the admin / workflow, not by submitters.
        read_only_fields = [
            'review_overseer', 'review_opened', 'review_closed', 'review_closes_at',
            'recommendation', 'current_step', 'step_status', 'submitted_at',
        ]


class SubmissionSerializer(serializers.ModelSerializer):
    """Public-facing serializer for the Step 1 submission pipeline."""
    class Meta:
        model = Entry
        fields = [
            'id', 'contest', 'entrant_name', 'work_title', 'work_subject', 'content',
            'original_location_url', 'original_location_label',
        ]

    def create(self, validated_data):
        # New submissions always enter the board at Step 1: Submission.
        validated_data['current_step'] = 1
        validated_data['step_status'] = 'Submission'
        return super().create(validated_data)


class ContestSerializer(serializers.ModelSerializer):
    entries = EntrySerializer(many=True, read_only=True)
    steps = serializers.SerializerMethodField()
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)

    class Meta:
        model = Contest
        fields = [
            'id', 'title', 'description', 'info_message', 'start_date', 'end_date',
            'is_active', 'entry_count', 'entries', 'steps',
        ]

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
