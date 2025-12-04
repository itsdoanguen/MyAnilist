from django.db import models
from django.utils import timezone
from .user import User


class AnimeNotificationPreference(models.Model):
    """
    User preferences for anime airing notifications
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='anime_notification_preference',
        primary_key=True
    )
    
    # Notification settings
    notify_before_hours = models.IntegerField(
        default=24,
        help_text='Notify user X hours before episode airs'
    )
    enabled = models.BooleanField(default=True)
    
    # Notification channels
    notify_by_email = models.BooleanField(default=True)
    notify_in_app = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'anime_notification_preferences'
        verbose_name = 'Anime Notification Preference'
        verbose_name_plural = 'Anime Notification Preferences'
    
    def __str__(self):
        return f"{self.user.username} - Notify {self.notify_before_hours}h before"


class AnimeAiringNotification(models.Model):
    """
    Scheduled notifications for anime episodes
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='scheduled_anime_notifications'
    )
    anilist_id = models.IntegerField(help_text='AniList anime ID')
    episode_number = models.IntegerField()
    
    # Airing info
    airing_at = models.DateTimeField(help_text='When the episode will air')
    notify_at = models.DateTimeField(help_text='When to send notification')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'anime_airing_notifications'
        verbose_name = 'Anime Airing Notification'
        verbose_name_plural = 'Anime Airing Notifications'
        indexes = [
            models.Index(fields=['notify_at', 'status'], name='idx_notify_status'),
            models.Index(fields=['user', 'anilist_id'], name='idx_user_anime'),
            models.Index(fields=['status', 'created_at'], name='idx_status_created'),
        ]
        unique_together = ['user', 'anilist_id', 'episode_number']
        ordering = ['-notify_at']
    
    def __str__(self):
        return f"{self.user.username} - Anime {self.anilist_id} Ep {self.episode_number} ({self.status})"
