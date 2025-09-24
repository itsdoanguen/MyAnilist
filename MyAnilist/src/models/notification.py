from django.db import models
from django.utils import timezone
from .user import User


class NotificationLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_logs')
    anilist_id = models.IntegerField()  # ID từ AniList API
    episode_number = models.IntegerField()
    sent_at = models.DateTimeField(default=timezone.now)
    notification_type = models.CharField(max_length=50, default='episode_release')
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'notification_logs'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Notification to {self.user.username} - Episode {self.episode_number} of AniList ID: {self.anilist_id}"