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
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Entry(models.Model):
    contest = models.ForeignKey(Contest, related_name='entries', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    author_in_game_name = models.CharField(max_length=50)
    content = models.TextField()
    original_board_link = models.URLField(blank=True)

    def __str__(self):
        return self.title

class Vote(models.Model):
    user = models.ForeignKey(User, related_name='votes', on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, related_name='votes', on_delete=models.CASCADE)
    score = models.IntegerField(default=1) # Can be used for ranking or point values

    class Meta:
        unique_together = ('user', 'entry') # A user can only vote for an entry once

    def __str__(self):
        return f"{self.user.username} voted for {self.entry.title}"
