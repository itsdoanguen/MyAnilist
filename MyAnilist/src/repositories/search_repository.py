import requests
import logging
from typing import List, Optional

from .anilist_querys import (
    ANIME_ID_SEARCH_QS, 
    ANIME_SEASON_TREND_QS, 
    ANIME_SEARCH_CRITERIA_QS
)

logger = logging.getLogger(__name__)


class SearchRepository:
    """
    Repository for search-related operations on AniList GraphQL API.
    Handles searching anime by name, criteria, and trending anime.
    """
    ANILIST_ENDPOINT = 'https://graphql.anilist.co'

    def search_media(self, query: str, page: int = 1, perpage: int = 10) -> List[dict]:
        """
        Search for anime by name/title.
        
        Args:
            query: Search query string
            page: Page number for pagination
            perpage: Number of items per page
            
        Returns:
            List of matching anime dictionaries
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        payload = {
            'query': ANIME_ID_SEARCH_QS, 
            'variables': {
                'query': query, 
                'page': page, 
                'perpage': perpage
            }
        }
        
        resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])
        
        return data.get('data', {}).get('Page', {}).get('media', [])

    def fetch_trending_anime_by_season(
        self, 
        season: str, 
        season_year: int, 
        page: int = 1, 
        perpage: int = 6
    ) -> List[dict]:
        """
        Fetch trending anime for a specific season and year.
        
        Args:
            season: Season (SPRING, SUMMER, FALL, WINTER)
            season_year: Year (e.g., 2025)
            page: Page number for pagination
            perpage: Number of items per page
            
        Returns:
            List of trending anime dictionaries
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        variables = {
            'season': season.upper(), 
            'seasonYear': int(season_year), 
            'page': page, 
            'perpage': perpage, 
            'sort': ['TRENDING_DESC', 'POPULARITY_DESC']
        }
        
        payload = {'query': ANIME_SEASON_TREND_QS, 'variables': variables}
        
        resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])
        
        return data.get('data', {}).get('Page', {}).get('media', [])

    def fetch_media_by_criteria(
        self, 
        genres: List[str] = None, 
        year: Optional[int] = None, 
        season: Optional[str] = None, 
        format: Optional[str] = None, 
        status: Optional[str] = None, 
        sort: str = None, 
        page: int = 1, 
        perpage: int = 10
    ) -> List[dict]:
        """
        Search for anime by multiple criteria.
        
        Args:
            genres: List of genre strings
            year: Year (e.g., 2025)
            season: Season (SPRING, SUMMER, FALL, WINTER)
            format: Format (TV, TV_SHORT, MOVIE, SPECIAL, OVA, ONA, MUSIC)
            status: Status (RELEASING, FINISHED, NOT_YET_RELEASED, CANCELLED, HIATUS)
            sort: Sort order (POPULARITY_DESC, SCORE_DESC, TRENDING_DESC, etc.)
            page: Page number for pagination
            perpage: Number of items per page
            
        Returns:
            List of matching anime dictionaries
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        variables = {
            'genres': genres if genres else None,
            'season': season.upper() if season else None,
            'seasonYear': int(year) if year else None,
            'format': format.upper() if format else None,
            'status': status.upper() if status else None,
            'page': page,
            'perpage': perpage,
            'sort': [sort.upper()] if sort else None, 
        }

        pruned_vars = {k: v for k, v in variables.items() if v is not None}
        logger.debug('fetch_media_by_criteria variables (pruned): %s', pruned_vars)
        
        payload = {'query': ANIME_SEARCH_CRITERIA_QS, 'variables': pruned_vars}
        
        resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
        
        # Log response for debugging
        if resp.status_code != 200:
            logger.error('AniList API error %d: %s', resp.status_code, resp.text)
        
        resp.raise_for_status()
        
        data = resp.json()
        if 'errors' in data:
            logger.error('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])

        media = data.get('data', {}).get('Page', {}).get('media', [])
        logger.debug('fetch_media_by_criteria returned %d media items', 
                    len(media) if media is not None else 0)

        return media