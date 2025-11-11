from django.urls import path
from .views.user_views import user_activity_heatmap, user_activity_list

urlpatterns = [
    path('<str:username>/overview/heatmap/', user_activity_heatmap, name='user_activity_heatmap'),
    path('<str:username>/overview/activity/', user_activity_list, name='user_activity_list'),
]