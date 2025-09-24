from django.db import models
from django.utils import timezone
from .user import User


class History(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    anilist_id = models.IntegerField()  # ID từ AniList API
    episode_number = models.IntegerField()
    watched_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'histories'
        verbose_name = 'Watch History'
        verbose_name_plural = 'Watch Histories'
        ordering = ['-watched_at']
    
    def __str__(self):
        return f"{self.user.username} - Episode {self.episode_number} of AniList ID: {self.anilist_id}"