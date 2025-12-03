from django.urls import path
from .views.user_views import (
    user_activity_heatmap, user_activity_list, user_anime_list, 
    search_users, upload_avatar, delete_avatar, get_user_profile, update_user_profile
)

urlpatterns = [
    path('search/', search_users, name='search_users'),
    path('avatar/upload/', upload_avatar, name='upload_avatar'),
    path('avatar/delete/', delete_avatar, name='delete_avatar'),
    path('profile/update/', update_user_profile, name='update_user_profile'),
    path('<str:username>/profile/', get_user_profile, name='user_profile'),
    path('<str:username>/overview/heatmap/', user_activity_heatmap, name='user_activity_heatmap'),
    path('<str:username>/overview/activity/', user_activity_list, name='user_activity_list'),
    path('<str:username>/animelist/', user_anime_list, name='user_anime_list'),
]