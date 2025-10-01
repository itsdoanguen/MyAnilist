from django.urls import path
from .views.anilist_views import anime, anime_by_name, anime_characters, trending_anime_by_season, anime_search

urlpatterns = [
    path('anime/<int:anime_id>/', anime, name='anilist_anime'),
    path('anime/<int:anime_id>/characters/', anime_characters, name='anilist_anime_characters'),
    path('anime/search/', anime_search, name='anilist_anime_search'),
    path('anime/by-name/', anime_by_name, name='anilist_anime_by_name'),
    path('anime/trending-by-season/', trending_anime_by_season, name='anilist_trending'),
]
