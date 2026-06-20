from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'College Chancellor'),
        ('voter', 'Qualified Voter'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='voter')
    is_verified = models.BooleanField(default=False)
    in_game_name = models.CharField(max_length=50, blank=True)


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
        ('Music', 'Music'),
        ('Other', 'Other'),
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

    contest = models.ForeignKey(Contest, related_name='entries', on_delete=models.CASCADE)

    # Core work identity
    entrant_name = models.CharField(max_length=80, help_text="Entrant's in-game name.")
    work_title = models.CharField(max_length=200)
    work_subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='Other')
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
    recommendation = models.CharField(
        max_length=20, choices=RECOMMENDATION_CHOICES, blank=True, default='',
    )

    # Workflow progress
    current_step = models.PositiveSmallIntegerField(default=1)
    step_status = models.CharField(
        max_length=60, default='Submission',
        help_text="Label for the current step, e.g. 'Loures Confirmation' or 'Nobility Awarded'.",
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

    def __str__(self):
        return f'{self.entrant_name}, "{self.work_title}"'


class Vote(models.Model):
    """A noble's review/recommendation on an entry (one per user per entry)."""
    RECOMMENDATION_CHOICES = Entry.RECOMMENDATION_CHOICES[1:]  # exclude 'Pending'

    user = models.ForeignKey(User, related_name='votes', on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, related_name='votes', on_delete=models.CASCADE)
    recommendation = models.CharField(
        max_length=20, choices=RECOMMENDATION_CHOICES, default='Village',
    )
    comment = models.TextField(blank=True)
    score = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'entry')  # A user can only review an entry once

    def __str__(self):
        return f"{self.user.username} recommended {self.recommendation} for {self.entry.work_title}"
