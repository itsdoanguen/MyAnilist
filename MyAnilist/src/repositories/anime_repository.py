import requests
import logging
from typing import List, Optional

from .anilist_querys import (
    ANIME_INFO_QS, 
    ANIME_CHARACTERS_QS, 
    ANIME_STAFF_QS, 
    ANIME_STATS_QS, 
    ANIME_WHERE_TO_WATCH_QS
)

logger = logging.getLogger(__name__)


class AnimeRepository:
    """
    Repository for anime-specific operations on AniList GraphQL API.
    Handles fetching anime details, characters, staff, stats, and streaming links.
    """
    ANILIST_ENDPOINT = 'https://graphql.anilist.co'

    def fetch_anime_by_id(self, anime_id: int) -> Optional[dict]:
        """
        Fetch detailed anime information by ID.
        
        Args:
            anime_id: AniList anime ID
            
        Returns:
            Dictionary containing anime details or None
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        payload = {'query': ANIME_INFO_QS, 'variables': {'id': anime_id}}
        try:
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.debug('AniList fetch_anime_by_id failed: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)
        
        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])
        
        return data.get('data', {}).get('Media')

    def fetch_characters_by_anime_id(
        self, 
        anime_id: int, 
        language: str = "JAPANESE", 
        page: int = 1, 
        perpage: int = 10
    ) -> List[dict]:
        """
        Fetch characters for a given anime ID.
        
        Args:
            anime_id: AniList anime ID
            language: Voice actor language filter (JAPANESE, ENGLISH, etc.)
            page: Page number for pagination
            perpage: Number of items per page
            
        Returns:
            List of character dictionaries
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        payload = {
            'query': ANIME_CHARACTERS_QS, 
            'variables': {
                'id': anime_id, 
                'page': page, 
                'perpage': perpage, 
                'language': language
            }
        }
        
        try:
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.debug('AniList characters query failed: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)

        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])

        return data.get('data', {}).get('Media', {}).get('characters', {}).get('edges', [])

    def fetch_staff_by_anime_id(
        self, 
        anime_id: int, 
        page: int = 1, 
        perpage: int = 10
    ) -> List[dict]:
        """
        Fetch staff for a given anime ID.
        
        Args:
            anime_id: AniList anime ID
            page: Page number for pagination
            perpage: Number of items per page
            
        Returns:
            List of staff dictionaries
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        payload = {
            'query': ANIME_STAFF_QS, 
            'variables': {
                'id': anime_id, 
                'page': page, 
                'perpage': perpage
            }
        }
        
        try:
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.debug('AniList staff query failed: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)

        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])

        return data.get('data', {}).get('Media', {}).get('staff', {}).get('edges', [])

    def fetch_stats_by_anime_id(self, anime_id: int) -> Optional[dict]:
        """
        Fetch statistics and rankings for a given anime ID.
        
        Args:
            anime_id: AniList anime ID
            
        Returns:
            Dictionary containing stats and rankings or None
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        payload = {'query': ANIME_STATS_QS, 'variables': {'id': anime_id}}
        
        try:
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.debug('AniList stats query failed: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)

        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])

        return data.get('data', {}).get('Media')
    
    def fetch_where_to_watch(self, anime_id: int) -> List[dict]:
        """
        Fetch streaming links for a given anime ID.
        
        Args:
            anime_id: AniList anime ID
            
        Returns:
            List of streaming platform dictionaries
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        payload = {'query': ANIME_WHERE_TO_WATCH_QS, 'variables': {'id': anime_id}}
        
        try:
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.debug('AniList where to watch query failed: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)

        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])

        return data.get('data', {}).get('Media', {}).get('streamingEpisodes', [])