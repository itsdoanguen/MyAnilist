from django.urls import path
from .list_views import list_create, list_get, user_lists_get, list_update

urlpatterns = [
    path('create/', list_create, name='list_create'),
    path('user/', user_lists_get, name='user_lists_get'),
    path('<int:list_id>/update/', list_update, name='list_update'),
    path('<int:anilist_id>/get/', list_get, name='list_get'),
]