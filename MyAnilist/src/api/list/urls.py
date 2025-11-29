from django.urls import path
from .list_views import list_create, list_get, user_lists_get, list_update, list_delete
from .user_list_views import (
    member_add, member_list, member_remove, member_permission_update, 
    join_request_create, join_request_list, join_request_respond, check_user_status
)
from .anime_list_views import anime_add, anime_list_get, anime_note_update, anime_remove

urlpatterns = [
    # List CRUD
    path('create/', list_create, name='list_create'),
    path('user/', user_lists_get, name='user_lists_get'),
    path('<int:list_id>/update/', list_update, name='list_update'),
    path('<int:list_id>/delete/', list_delete, name='list_delete'),
    
    # Member management
    path('member/<int:list_id>/add/', member_add, name='member_add'),
    path('member/<int:list_id>/list/', member_list, name='member_list'),
    path('member/<int:list_id>/remove/', member_remove, name='member_remove'),
    path('member/<int:list_id>/permission/', member_permission_update, name='member_permission_update'),
    path('member/<int:list_id>/status/', check_user_status, name='check_user_status'),
    
    # Join requests
    path('<int:list_id>/request-join/', join_request_create, name='join_request_create'),
    path('<int:list_id>/requests/', join_request_list, name='join_request_list'),
    path('<int:list_id>/requests/<int:request_id>/respond/', join_request_respond, name='join_request_respond'),
    
    # Anime in list management
    path('anime/<int:list_id>/add/', anime_add, name='anime_add'),
    path('anime/<int:list_id>/', anime_list_get, name='anime_list_get'),
    path('anime/<int:list_id>/<int:anilist_id>/update/', anime_note_update, name='anime_note_update'),
    path('anime/<int:list_id>/<int:anilist_id>/remove/', anime_remove, name='anime_remove'),
]