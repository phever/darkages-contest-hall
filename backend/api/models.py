import secrets
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'College Chancellor'),
        ('voter', 'Qualified Voter'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='voter')
    is_verified = models.BooleanField(default=False)
    in_game_name = models.CharField(max_length=50, blank=True)


def _default_invite_expiry():
    return timezone.now() + timedelta(days=14)


class Invitation(models.Model):
    """
    A Chancellor's invitation for a new noble to create an account.

    The Chancellor sets the invitee's email and in-game name; the noble accepts
    via an emailed token link, choosing only a username and password. The email
    and in-game name are fixed by the Chancellor and cannot be changed by the
    noble. Accepting creates a verified voter account.
    """
    email = models.EmailField()
    in_game_name = models.CharField(max_length=50, blank=True)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    invited_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='sent_invitations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=_default_invite_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='accepted_invitation',
    )

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

    @property
    def is_accepted(self):
        return self.accepted_at is not None

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def status(self):
        if self.is_accepted:
            return 'accepted'
        if self.is_expired:
            return 'expired'
        return 'pending'

    def __str__(self):
        return f"Invitation for {self.email} ({self.status})"


class Contest(models.Model):
    """A contest board (e.g. the Mileth College Contest Hall) that groups submissions."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    info_message = models.TextField(
        blank=True,
        help_text="Notice shown at the top of the board (e.g. review/recognition requirements).",
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class WorkflowStep(models.Model):
    """One of the steps a submission passes through (Submission -> Nobility Awarded)."""
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Step {self.number}/4: {self.title}"


class Entry(models.Model):
    SUBJECT_CHOICES = (
        ('Art', 'Art'),
        ('Literature', 'Literature'),
        ('Lore', 'Lore'),
        ('Philosophy', 'Philosophy'),
        ('History', 'History'),
        ('Persona', 'Persona'),
    )
    # Recognition levels that may be recommended for a work.
    RECOMMENDATION_CHOICES = (
        ('', 'Pending'),
        ('Village', 'Village'),
        ('Clave', 'Clave'),
        ('Kingdom', 'Kingdom'),
        ('Aisling', 'Aisling'),
        ('No Award', 'No Award'),
    )
    TOTAL_STEPS = 4
    # Label shown for each workflow position (mirrors the College progress board).
    STEP_LABELS = {
        1: 'Submission',
        2: 'Review',
        3: 'Loures Confirmation',
        4: 'Nobility Awarded',
    }

    contest = models.ForeignKey(Contest, related_name='entries', on_delete=models.CASCADE)

    # Core work identity
    entrant_name = models.CharField(max_length=80, help_text="Entrant's in-game name.")
    work_title = models.CharField(max_length=200)
    work_subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='Literature')
    content = models.TextField(blank=True, help_text="Submission text or archived content.")

    # Where the work lives
    original_location_url = models.URLField(blank=True)
    original_location_label = models.CharField(
        max_length=120, blank=True,
        help_text="Shown when there is no URL, e.g. '[Post 414 on College Contest Board]'.",
    )
    archived_location_url = models.CharField(
        max_length=400, blank=True,
        help_text="Link to the archived copy of the work.",
    )

    # Review metadata (mirrors the College progress board)
    review_overseer = models.CharField(max_length=80, blank=True)
    review_opened = models.CharField(max_length=20, blank=True, help_text="In-game date, e.g. 220.02.16")
    review_closed = models.CharField(max_length=20, blank=True, help_text="In-game date, e.g. 220.06.18")
    review_closes_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Planned end of the review/voting period — used for noble reminders.",
    )
    recommendation = models.CharField(
        max_length=20, choices=RECOMMENDATION_CHOICES, blank=True, default='',
    )

    # Workflow progress
    current_step = models.PositiveSmallIntegerField(default=1)
    step_status = models.CharField(
        max_length=60, default='Submission',
        help_text="Label for the current step, e.g. 'Loures Confirmation' or 'Nobility Awarded'.",
    )

    # Archive: older works kept for posterity. Archived entries are hidden from
    # the live progress board and shown in the searchable Archive section instead.
    is_archived = models.BooleanField(
        default=False,
        help_text="Show this work in the Archive (older submissions) instead of the live board.",
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'entries'
        # Mirror the College board: most recently opened reviews first. The in-game
        # date format (YYY.MM.DD, zero-padded) sorts correctly as a string.
        ordering = ['-review_opened', '-submitted_at']

    @property
    def on_step(self):
        return f"{self.current_step}/{self.TOTAL_STEPS} - {self.step_status}"

    @property
    def progress_text(self):
        return f"{self.current_step}/{self.TOTAL_STEPS}"

    def advance_step(self):
        """Move this entry to the next workflow step. Returns True if it advanced,
        False if it was already at the final step (Nobility Awarded)."""
        if self.current_step >= self.TOTAL_STEPS:
            return False
        self.current_step += 1
        self.step_status = self.STEP_LABELS.get(self.current_step, self.step_status)
        self.save(update_fields=['current_step', 'step_status', 'updated_at'])
        return True

    def __str__(self):
        return f'{self.entrant_name}, "{self.work_title}"'


class VoteIntention(models.Model):
    """
    A noble's PRIVATE intended recommendation and draft review for an entry.

    Real voting/reviewing happens in the in-game Contest Hall — this is a private
    scratchpad a noble can prepare here and copy-paste in game. Visible only to its
    author and to Chancellors (enforced in the API). One per user per entry.
    """
    RECOMMENDATION_CHOICES = (
        ('', 'Undecided'),
        ('Village', 'Village'),
        ('Clave', 'Clave'),
        ('Kingdom', 'Kingdom'),
        ('Aisling', 'Aisling'),
        ('No Award', 'No Award'),
    )

    user = models.ForeignKey(User, related_name='vote_intentions', on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, related_name='vote_intentions', on_delete=models.CASCADE)
    recommendation = models.CharField(
        max_length=20, choices=RECOMMENDATION_CHOICES, blank=True, default='',
    )
    review_text = models.TextField(
        blank=True, help_text="Draft review to copy-paste into the in-game Contest Hall.",
    )
    remind_before_close = models.BooleanField(
        default=False, help_text="Email this noble before the review period ends.",
    )
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'entry')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s intention for \"{self.entry.work_title}\""
