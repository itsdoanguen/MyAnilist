from django.db import models
from django.utils import timezone
from .user import User


class UserActivity(models.Model):
    """Track user activities for activity feed and auditing.

    This model is intentionally simple and generic:
    - `action_type` describes the kind of activity (e.g. "followed_anime", "rated", "created_list").
    - `target_type` and `target_id` allow referencing arbitrary external objects (AniList ids or internal objects).
    - `metadata` stores any additional JSON data relevant to the action (score, comment snippet, list name, etc.).
    """

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=64)

    target_type = models.CharField(max_length=64, null=True, blank=True)
    target_id = models.BigIntegerField(null=True, blank=True)

    # Free-form JSON data for extra context (e.g. {'score': 9, 'comment': 'Great episode!'})
    metadata = models.JSONField(default=dict, blank=True)

    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type']),
        ]

    def __str__(self):
        target = f"{self.target_type}:{self.target_id}" if self.target_type or self.target_id else ""
        return f"{self.user.username} {self.action_type} {target}"
