from django.db import models
from django.utils import timezone
from .user import User


class List(models.Model):
    list_id = models.AutoField(primary_key=True)
    list_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    isPrivate = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#3498db')  # Hex color code
    
    # Thêm field description cho list
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
    
    # Thêm field để xác định quyền của user với list
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
    
    # Thêm field để lưu thêm thông tin
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