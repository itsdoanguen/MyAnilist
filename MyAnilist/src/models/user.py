from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    # Loại bỏ user_id và sử dụng id mặc định từ AbstractUser
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    date_join = models.DateTimeField(default=timezone.now)
    
    # Override username field để sử dụng email làm username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username