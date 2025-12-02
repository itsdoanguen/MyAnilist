from django.db import models
from django.utils import timezone
from .user import User
from .list import List


class ListLike(models.Model):
    """Model to track users who like/favorite lists."""
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='liked_lists',
        help_text="User who likes the list"
    )
    list = models.ForeignKey(
        List, 
        on_delete=models.CASCADE, 
        related_name='likes',
        help_text="The list being liked"
    )
    liked_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the user liked this list"
    )
    
    class Meta:
        db_table = 'list_likes'
        unique_together = ['user', 'list']  
        verbose_name = 'List Like'
        verbose_name_plural = 'List Likes'
        ordering = ['-liked_at']
        indexes = [
            models.Index(fields=['user', '-liked_at']),
            models.Index(fields=['list', '-liked_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} likes {self.list.list_name}"
