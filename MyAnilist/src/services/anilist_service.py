from typing import List, Optional
from ..repositories.anilist_repository import AnilistRepository
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

        return {
            'id': media.get('id'),
            'name_romaji': title.get('romaji'),
            'name_english': title.get('english'),
            'starting_time': self._fmt_date(start),
            'ending_time': self._fmt_date(end),
            'cover_image': (media.get('coverImage') or {}).get('large'),
            'banner_image': media.get('bannerImage'),
            'airing_format': media.get('format'),
            'airing_status': media.get('status'),
            'airing_episodes': media.get('episodes'),
            'season': media.get('season'),
            'desc': media.get('description'),
            'average_score': media.get('averageScore'),
            'genres': media.get('genres'),
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
