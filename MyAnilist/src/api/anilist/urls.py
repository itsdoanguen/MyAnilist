from django.urls import path
from .views.anime_views import anime_detail, anime_overview, anime_characters, anime_staff
from .views.search_views import search_by_criteria, search_by_name, search_trending

urlpatterns = [
    # Anime detail endpoints
    path('anime/<int:anime_id>/', anime_detail, name='anilist_anime_detail'),           # Basic info 
    path('anime/<int:anime_id>/overview/', anime_overview, name='anilist_anime_overview'),  # Overview tab
    path('anime/<int:anime_id>/characters/', anime_characters, name='anilist_anime_characters'),  # Characters tab
    path('anime/<int:anime_id>/staffs/', anime_staff, name='anilist_anime_staffs'),       # Staff tab
    
    # Search endpoints
    path('search/criteria/', search_by_criteria, name='anilist_search_criteria'),
    path('search/name/', search_by_name, name='anilist_search_name'),
    path('search/trending/', search_trending, name='anilist_search_trending'),
]
