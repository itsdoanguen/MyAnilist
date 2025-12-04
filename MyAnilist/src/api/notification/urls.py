from django.urls import path
from .notification_views import (
    notification_preferences,
    my_notifications,
    cancel_anime_notifications,
)

urlpatterns = [
    path('preferences/', notification_preferences, name='notification_preferences'),
    path('my/', my_notifications, name='my_notifications'),
    path('cancel/<int:anilist_id>/', cancel_anime_notifications, name='cancel_anime_notifications'),
]
