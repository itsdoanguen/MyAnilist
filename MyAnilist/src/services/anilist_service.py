from typing import List, Optional
from ..repositories.anilist_repository import AnilistRepository
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class AnilistService:
    """Service layer to perform business logic and parsing for AniList responses."""

    def __init__(self):
        self.repo = AnilistRepository()

    def _fmt_date(self, d: dict) -> Optional[str]:
        if not d:
            return None
        y = d.get('year')
        m = d.get('month')
        day = d.get('day')
        if y and m and day:
            return f"{m}/{day}/{y}"
        return None

    def parse_media(self, media: dict) -> dict:
        title = media.get('title') or {}
        start = media.get('startDate') or {}
        end = media.get('endDate') or {}
        studios_nodes = (media.get('studios') or {}).get('nodes') if media.get('studios') else None
        studios = [s.get('name') for s in studios_nodes] if studios_nodes else []
        tags_nodes = (media.get('tags') or [])
        tags = [t.get('name') for t in tags_nodes][:10]

        return {
            'id': media.get('id'),
            'name_romaji': title.get('romaji'),
            'name_english': title.get('english'),
            'name_native': title.get('native'),
            'synonyms': media.get('synonyms') or [],
            'starting_time': self._fmt_date(start),
            'ending_time': self._fmt_date(end),
            'cover_image': (media.get('coverImage') or {}).get('large'),
            'banner_image': media.get('bannerImage'),
            'airing_format': media.get('format'),
            'airing_status': media.get('status'),
            'airing_episodes': media.get('episodes'),
            'duration': media.get('duration'),
            'season': media.get('season'),
            'season_year': media.get('seasonYear'),
            'desc': media.get('description'),
            'average_score': media.get('averageScore'),
            'mean_score': media.get('meanScore'),
            'popularity': media.get('popularity'),
            'favourites': media.get('favourites'),
            'trailer': media.get('trailer'),
            'genres': (media.get('genres') or [])[:10],
            'tags': tags,
            'source': media.get('source'),
            'hashtag': media.get('hashtag'),
            'studios': studios,
            'next_airing_ep': media.get('nextAiringEpisode'),
        }

    def get_by_id(self, anime_id: int) -> dict:
        media = self.repo.fetch_anime_by_id(anime_id)
        if not media:
            raise LookupError('Anime not found')
        return self.parse_media(media)

    def search_and_get_first(self, query: str) -> dict:
        media_list = self.repo.search_media(query)
        if not media_list:
            raise LookupError('No search results')
        first = media_list[0]
        return self.get_by_id(first.get('id'))

    def search_candidates(self, query: str, page: int = 1, perpage: int = 10) -> List[dict]:
        media_list = self.repo.search_media(query, page, perpage)
        # map to candidate shape
        candidates = []
        for m in media_list:
            candidates.append({
                'id': m.get('id'),
                'romaji': (m.get('title') or {}).get('romaji'),
                'english': (m.get('title') or {}).get('english'),
                'cover': (m.get('coverImage') or {}).get('large'),
                'average_score': m.get('averageScore'),
                'episodes': m.get('episodes'),
                'season': m.get('season'),
            })
        return candidates

    def get_trending_anime_by_season(self, season: str = None, season_year: int = None, page: int = 1, perpage: int = 6) -> List[dict]:
        """Fetch trending anime for a given season/year.

        Defaults to 2025/FALL when season or season_year aren't provided.
        Returns parsed media list filtered to those with upcoming episodes and sorted by trending/popularity/averageScore.
        """
        # If season/year not provided, compute current season/year dynamically
        if season is None or season_year is None:
            current_season, current_year = self._current_season_year()
            if season is None:
                season = current_season
            if season_year is None:
                season_year = current_year

        try:
            media_list = self.repo.fetch_trending_anime_by_season(season, season_year, page, perpage)
        except Exception:
            logger.exception('Failed to fetch season trending anime')
            return []

        # Filter to those with upcoming episodes (nextAiringEpisode present)
        upcoming = [m for m in media_list if m.get('nextAiringEpisode')]

        # Sort by trending, then popularity, then averageScore (desc)
        def score_key(m):
            return (
                m.get('trending') or 0,
                m.get('popularity') or 0,
                m.get('averageScore') or 0,
            )

        upcoming_sorted = sorted(upcoming, key=score_key, reverse=True)
        return [self.parse_media(m) for m in upcoming_sorted]

    def _current_season_year(self) -> tuple:
        """Return (season, year) for the current date.

        Seasons mapping (anime industry standard approximation):
        - WINTER: Jan(1) - Mar(3)
        - SPRING: Apr(4) - Jun(6)
        - SUMMER: Jul(7) - Sep(9)
        - FALL:   Oct(10) - Dec(12)
        """
        now = timezone.now()
        month = now.month
        year = now.year

        if 1 <= month <= 3:
            season = 'WINTER'
        elif 4 <= month <= 6:
            season = 'SPRING'
        elif 7 <= month <= 9:
            season = 'SUMMER'
        else:
            season = 'FALL'

        return season, year

    def get_trending_anime_by_season_default(self, page: int = 1, perpage: int = 6) -> List[dict]:
        """Backward-compatible no-arg wrapper used by views: uses dynamic current season/year."""
        return self.get_trending_anime_by_season(season=None, season_year=None, page=page, perpage=perpage)

    def search_by_criteria(self, genres: List[str] = None, year: int = None, season: str = None, format: List[str] = None, status: str = None, sort: str = None, page: int = 1, perpage: int = 10) -> List[dict]:
        """Search for anime by multiple criteria including genres, year, season, format, and status."""

        # normalize defaults
        if genres is None:
            genres = []
        if format is None:
            format = []

        try:
            media_list = self.repo.fetch_media_by_criteria(genres=genres, year=year, season=season, format=format, status=status, sort=sort, page=page, perpage=perpage)
        except Exception:
            logger.exception('Failed to fetch anime by criteria')
            return []

        if not media_list:
            return []

        return [self.parse_media(m) for m in media_list]
    
    def get_characters_by_anime_id(self, anime_id: int, language: str = "JAPANESE", page: int = 1, perpage: int = 10) -> List[dict]:
        """Fetch characters for a given anime ID.

        Returns a list of characters. Each character includes:
        - id, name_full, image, role, voice_actors: [ {id, name_full, name_native, image, language} ]
        """
        try:
            characters = self.repo.fetch_characters_by_anime_id(anime_id, language=language, page=page, perpage=perpage)
        except Exception:
            logger.exception('Failed to fetch characters for anime id %s', anime_id)
            return []

        if not characters:
            return []

        result = []
        for char in characters:
            node = char.get('node') or {}
            role = char.get('role')
            image = (node.get('image') or {}).get('large')

            vactors_raw = char.get('voiceActors') or []
            voice_actors = []
            lang_filter = (language or '').strip().upper() if language is not None else ''
            for va in vactors_raw:
                va_node = va or {}
                va_name = (va_node.get('name') or {})
                va_image = (va_node.get('image') or {}).get('large')
                va_lang = (va_node.get('language') or '').strip().upper()
                if lang_filter and lang_filter != 'ALL' and va_lang != lang_filter:
                    continue
                voice_actors.append({
                    'id': va_node.get('id'),
                    'name_full': va_name.get('full'),
                    'name_native': va_name.get('native'),
                    'image': va_image,
                    'language': va_node.get('language')
                })

            result.append({
                'id': node.get('id'),
                'name_full': (node.get('name') or {}).get('full'),
                'image': image,
                'role': role,
                'voice_actors': voice_actors,
            })
        return result
