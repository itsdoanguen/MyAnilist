from django.urls import path
from .views.user_views import user_activity_heatmap, user_activity_list, user_anime_list, search_users

urlpatterns = [
    path('search/', search_users, name='search_users'),
    path('<str:username>/overview/heatmap/', user_activity_heatmap, name='user_activity_heatmap'),
    path('<str:username>/overview/activity/', user_activity_list, name='user_activity_list'),
    path('<str:username>/animelist/', user_anime_list, name='user_anime_list'),
]