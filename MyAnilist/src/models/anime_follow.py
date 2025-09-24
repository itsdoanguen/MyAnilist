from django.db import models
from django.utils import timezone
from .user import User


class AnimeFollow(models.Model):
    WATCH_STATUS_CHOICES = [
        ('watching', 'Watching'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
        ('plan_to_watch', 'Plan to Watch'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='anime_follows')
    anilist_id = models.IntegerField()  # ID từ AniList API
    notify_email = models.BooleanField(default=False)
    episode_progress = models.IntegerField(default=0)
    watch_status = models.CharField(max_length=20, choices=WATCH_STATUS_CHOICES, default='plan_to_watch')
    isFavorite = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    total_rewatch = models.IntegerField(default=0)
    user_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'anime_follows'
        unique_together = ['user', 'anilist_id']
        verbose_name = 'Anime Follow'
        verbose_name_plural = 'Anime Follows'
    
    def __str__(self):
        return f"{self.user.username} - AniList ID: {self.anilist_id}"