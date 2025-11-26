from django.urls import path
from .list_views import list_create, list_get, user_lists_get, list_update, list_delete
from .user_list_views import member_add, member_list, member_remove, member_permission_update

urlpatterns = [
    path('create/', list_create, name='list_create'),
    path('user/', user_lists_get, name='user_lists_get'),
    path('<int:list_id>/update/', list_update, name='list_update'),
    path('<int:list_id>/delete/', list_delete, name='list_delete'),
    path('member/<int:list_id>/add/', member_add, name='member_add'),
    path('member/<int:list_id>/list/', member_list, name='member_list'),
    path('member/<int:list_id>/remove/', member_remove, name='member_remove'),
    path('member/<int:list_id>/permission/', member_permission_update, name='member_permission_update'),
]