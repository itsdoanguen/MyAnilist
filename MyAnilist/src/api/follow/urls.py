from django.urls import path
from .follow_views import follow_get, follow_create, follow_update, follow_delete

urlpatterns = [
    path('<int:anilist_id>/get/', follow_get, name='follow_get'),
    path('<int:anilist_id>/create/', follow_create, name='follow_create'),
    path('<int:anilist_id>/update/', follow_update, name='follow_update'),
    path('<int:anilist_id>/delete/', follow_delete, name='follow_delete'),
]
