from django.db import models
from django.utils import timezone
from .user import User


class List(models.Model):
    list_id = models.AutoField(primary_key=True)
    list_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    isPrivate = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#3498db')  # Hex color code
    
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lists'
        verbose_name = 'List'
        verbose_name_plural = 'Lists'
    
    def __str__(self):
        return self.list_name


class UserList(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_lists')
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='user_lists')
    
    is_owner = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_lists'
        unique_together = ['user', 'list']
        verbose_name = 'User List'
        verbose_name_plural = 'User Lists'
    
    def __str__(self):
        return f"{self.user.username} - {self.list.list_name}"


class AnimeList(models.Model):
    id = models.AutoField(primary_key=True)
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='anime_items')
    anilist_id = models.IntegerField()  # ID từ AniList API
    added_date = models.DateTimeField(default=timezone.now)
    
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True)
    
    class Meta:
        db_table = 'anime_lists'
        unique_together = ['list', 'anilist_id']
        verbose_name = 'Anime List Item'
        verbose_name_plural = 'Anime List Items'
        ordering = ['-added_date']
    
    def __str__(self):
        return f"{self.list.list_name} - AniList ID: {self.anilist_id}"


class ListJoinRequest(models.Model):
    """Model for users requesting to join a list or request edit permission."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    REQUEST_TYPE_CHOICES = [
        ('join', 'Join List'),
        ('edit_permission', 'Request Edit Permission'),
    ]
    
    request_id = models.AutoField(primary_key=True)
    list = models.ForeignKey(
        List, 
        on_delete=models.CASCADE, 
        related_name='join_requests'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='list_join_requests'
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='join',
        help_text="Type of request: join (become member) or edit_permission (upgrade to editor)"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    message = models.TextField(blank=True, default='')  
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='responded_join_requests'
    )
    
    class Meta:
        db_table = 'list_join_requests'
        unique_together = ['list', 'user', 'status', 'request_type']  
        verbose_name = 'List Request'
        verbose_name_plural = 'List Requests'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.list.list_name} ({self.request_type}: {self.status})"