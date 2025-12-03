import requests
import logging
import time
from typing import List, Optional

from .anilist_querys import (
    ANIME_INFO_QS,
    ANIME_INFO_LIGHTWEIGHT_QS,
    ANIME_BATCH_INFO_QS,
    ANIME_COVERS_BATCH_QS,
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
        start_time = time.time()
        payload = {'query': ANIME_INFO_QS, 'variables': {'id': anime_id}}
        try:
            request_start = time.time()
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            request_duration = time.time() - request_start
            resp.raise_for_status()
            
            parse_start = time.time()
            data = resp.json()
            parse_duration = time.time() - parse_start
            
            total_duration = time.time() - start_time
            logger.debug(f'[API] fetch_anime_by_id({anime_id}): total={total_duration:.3f}s, request={request_duration:.3f}s, parse={parse_duration:.3f}s')
            
        except requests.exceptions.HTTPError as e:
            duration = time.time() - start_time
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.warning(f'[API] fetch_anime_by_id({anime_id}) FAILED after {duration:.3f}s: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)
        
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])
        
        return data.get('data', {}).get('Media')

    def fetch_anime_basic_info(self, anime_id: int) -> Optional[dict]:
        """
        Fetch lightweight anime information (only title, cover, episodes).
        Use this for anime list displays to reduce API response size and improve performance.
        
        Args:
            anime_id: AniList anime ID
            
        Returns:
            Dictionary containing basic anime info or None
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        start_time = time.time()
        payload = {'query': ANIME_INFO_LIGHTWEIGHT_QS, 'variables': {'id': anime_id}}
        try:
            request_start = time.time()
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            request_duration = time.time() - request_start
            resp.raise_for_status()
            
            parse_start = time.time()
            data = resp.json()
            parse_duration = time.time() - parse_start
            
            total_duration = time.time() - start_time
            logger.debug(f'[API] fetch_anime_basic_info({anime_id}): total={total_duration:.3f}s, request={request_duration:.3f}s, parse={parse_duration:.3f}s')
            
        except requests.exceptions.HTTPError as e:
            duration = time.time() - start_time
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.warning(f'[API] fetch_anime_basic_info({anime_id}) FAILED after {duration:.3f}s: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)
        
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])
        
        return data.get('data', {}).get('Media')

    def fetch_anime_batch(self, anime_ids: List[int]) -> dict:
        """
        Fetch multiple anime in a single API request (up to 50 anime).
        
        Args:
            anime_ids: List of AniList anime IDs (max 50)
            
        Returns:
            Dictionary mapping anime_id -> anime_data
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        if not anime_ids:
            return {}
        
        if len(anime_ids) > 50:
            logger.warning(f'fetch_anime_batch called with {len(anime_ids)} IDs, will only fetch first 50')
            anime_ids = anime_ids[:50]
        
        start_time = time.time()
        payload = {'query': ANIME_BATCH_INFO_QS, 'variables': {'ids': anime_ids}}
        
        try:
            request_start = time.time()
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=15)
            request_duration = time.time() - request_start
            resp.raise_for_status()
            
            parse_start = time.time()
            data = resp.json()
            parse_duration = time.time() - parse_start
            
            total_duration = time.time() - start_time
            logger.info(f'[API] fetch_anime_batch({len(anime_ids)} anime): total={total_duration:.3f}s, request={request_duration:.3f}s, parse={parse_duration:.3f}s')
            
        except requests.exceptions.HTTPError as e:
            duration = time.time() - start_time
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.warning(f'[API] fetch_anime_batch FAILED after {duration:.3f}s: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)
        
        if 'errors' in data:
            logger.warning('AniList batch query returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])
        
        media_list = data.get('data', {}).get('Page', {}).get('media', [])
        result = {}
        for anime in media_list:
            if anime and 'id' in anime:
                result[anime['id']] = anime
        
        logger.debug(f'[API] fetch_anime_batch: requested {len(anime_ids)}, received {len(result)}')
        return result

    def fetch_characters_by_anime_id(
        self, 
        anime_id: int, 
        language: str = "JAPANESE", 
        page: int = 1, 
        perpage: int = 10
    ) -> dict:
        """
        Fetch characters for a given anime ID.
        
        Args:
            anime_id: AniList anime ID
            language: Voice actor language filter (JAPANESE, ENGLISH, etc.)
            page: Page number for pagination
            perpage: Number of items per page
            
        Returns:
            Dictionary with pageInfo and edges (list of character dictionaries)
            
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

        characters_data = data.get('data', {}).get('Media', {}).get('characters', {})
        return {
            'pageInfo': characters_data.get('pageInfo', {}),
            'edges': characters_data.get('edges', [])
        }

    def fetch_staff_by_anime_id(
        self, 
        anime_id: int, 
        page: int = 1, 
        perpage: int = 10
    ) -> dict:
        """
        Fetch staff for a given anime ID.
        
        Args:
            anime_id: AniList anime ID
            page: Page number for pagination
            perpage: Number of items per page
            
        Returns:
            Dictionary with pageInfo and edges (list of staff dictionaries)
            
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

        staff_data = data.get('data', {}).get('Media', {}).get('staff', {})
        return {
            'pageInfo': staff_data.get('pageInfo', {}),
            'edges': staff_data.get('edges', [])
        }

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
    
    def fetch_anime_covers_batch(self, anime_ids: List[int]) -> dict:
        """
        Fetch only cover images for multiple anime in a single API request (up to 50 anime).
        This is optimized for getting just covers without other anime data.
        
        Args:
            anime_ids: List of AniList anime IDs (max 50)
            
        Returns:
            Dictionary mapping anime_id -> cover_image_url
            
        Raises:
            RuntimeError: If API request fails or returns errors
        """
        if not anime_ids:
            return {}
        
        if len(anime_ids) > 50:
            logger.warning(f'fetch_anime_covers_batch called with {len(anime_ids)} IDs, will only fetch first 50')
            anime_ids = anime_ids[:50]
        
        start_time = time.time()
        payload = {'query': ANIME_COVERS_BATCH_QS, 'variables': {'ids': anime_ids}}
        
        try:
            request_start = time.time()
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=15)
            request_duration = time.time() - request_start
            resp.raise_for_status()
            
            parse_start = time.time()
            data = resp.json()
            parse_duration = time.time() - parse_start
            
            total_duration = time.time() - start_time
            logger.info(f'[API] fetch_anime_covers_batch({len(anime_ids)} covers): total={total_duration:.3f}s, request={request_duration:.3f}s, parse={parse_duration:.3f}s')
            
        except requests.exceptions.HTTPError as e:
            duration = time.time() - start_time
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.warning(f'[API] fetch_anime_covers_batch FAILED after {duration:.3f}s: status=%s body=%s', 
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)
        
        if 'errors' in data:
            logger.warning('AniList covers batch query returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])
        
        media_list = data.get('data', {}).get('Page', {}).get('media', [])
        result = {}
        for anime in media_list:
            if anime and 'id' in anime:
                cover_url = (anime.get('coverImage') or {}).get('large')
                result[anime['id']] = cover_url
        
        logger.debug(f'[API] fetch_anime_covers_batch: requested {len(anime_ids)}, received {len(result)}')
        return result