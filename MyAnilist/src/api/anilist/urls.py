from django.urls import path
from .views.anilist_views import anime, anime_by_name

urlpatterns = [
    path('anime/', anime, name='anilist_anime'),
    path('anime-by-name/', anime_by_name, name='anilist_anime_by_name'),
]
