import requests
import logging
from typing import List, Optional

from .anilist_querys import ANIME_CHARACTERS_QS, ANIME_STAFF_QS, ANIME_INFO_QS, ANIME_ID_SEARCH_QS, ANIME_SEASON_TREND_QS

logger = logging.getLogger(__name__)


class AnilistRepository:
	"""Repository responsible for making HTTP requests to the AniList GraphQL API
	and returning raw media dictionaries (no transformation).
	"""
	ANILIST_ENDPOINT = 'https://graphql.anilist.co'

	def fetch_anime_by_id(self, anime_id: int) -> Optional[dict]:
		payload = {'query': ANIME_INFO_QS, 'variables': {'id': anime_id}}
		try:
			resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
			resp.raise_for_status()
		except requests.exceptions.HTTPError as e:
			body = e.response.text if getattr(e, 'response', None) is not None else str(e)
			logger.debug('AniList fetch_anime_by_id failed: status=%s body=%s', getattr(e.response, 'status_code', None), body)
			raise RuntimeError(body)
		data = resp.json()
		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])
		return data.get('data', {}).get('Media')

	def search_media(self, query: str, page: int = 1, perpage: int = 10) -> List[dict]:
		payload = {'query': ANIME_ID_SEARCH_QS, 'variables': {'query': query, 'page': page, 'perpage': perpage}}
		resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
		resp.raise_for_status()
		data = resp.json()
		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])
		return data.get('data', {}).get('Page', {}).get('media', [])

	def fetch_trending_anime_by_season(self, season: str, season_year: int, page: int = 1, perpage: int = 6) -> List[dict]:
		# season should be one of: SPRING, SUMMER, FALL, WINTER
		variables = {'season': season.upper(), 'seasonYear': int(season_year), 'page': page, 'perpage': perpage, 'sort': ['TRENDING_DESC', 'POPULARITY_DESC']}
		payload = {'query': ANIME_SEASON_TREND_QS, 'variables': variables}
		resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
		resp.raise_for_status()
		data = resp.json()
		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])
		return data.get('data', {}).get('Page', {}).get('media', [])

	def fetch_media_by_criteria(self, genres: List[str] = None, year: Optional[int] = None, season: Optional[str] = None, format: List[str] = None, status: Optional[str] = None, sort: str = None, page: int = 1, perpage: int = 10) -> List[dict]:
		# season should be one of: SPRING, SUMMER, FALL, WINTER
		# format should be one of: TV_SHOW, TV_SHORT, MOVIE, SPECIAL, OVA, ONA, MUSIC
		# status should be one of: AIRING, FINISHED, NOT_YET_RELEASE, CANCELLED

		variables = {
			'genres': genres if genres else None,
			'season': season.upper() if season else None,
			'seasonYear': int(year) if year else None,
			'format': format if format else None,
			'status': status.upper() if status else None,
			'page': page,
			'perpage': perpage,
			'sort': sort.upper() if sort else None,
		}

		# use the criteria search query
		from .anilist_querys import ANIME_SEARCH_CRITERIA_QS

		# prune None values so GraphQL filters are not applied unintentionally
		pruned_vars = {k: v for k, v in variables.items() if v is not None}
		logger.debug('fetch_media_by_criteria variables (pruned): %s', pruned_vars)
		payload = {'query': ANIME_SEARCH_CRITERIA_QS, 'variables': pruned_vars}
		resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
		resp.raise_for_status()
		data = resp.json()

		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])

		media = data.get('data', {}).get('Page', {}).get('media', [])
		logger.debug('fetch_media_by_criteria returned %d media items', len(media) if media is not None else 0)

		return media

	def fetch_characters_by_anime_id(self, anime_id: int, language: str = "JAPANESE", page: int = 1, perpage: int = 10) -> List[dict]:
		payload = {'query': ANIME_CHARACTERS_QS, 'variables': {'id': anime_id, 'page': page, 'perpage': perpage, 'language': language}}
		try:
			resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
			resp.raise_for_status()
		except requests.exceptions.HTTPError as e:
			# log full response body for debugging
			body = e.response.text if getattr(e, 'response', None) is not None else str(e)
			logger.debug('AniList characters query failed: status=%s body=%s', getattr(e.response, 'status_code', None), body)
			raise RuntimeError(body)

		data = resp.json()
		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])

		return data.get('data', {}).get('Media', {}).get('characters', {}).get('edges', [])

	def fetch_staff_by_anime_id(self, anime_id: int, page: int = 1, perpage: int = 10) -> List[dict]:
		"""Fetch staff for a given anime ID from AniList."""
		payload = {'query': ANIME_STAFF_QS, 'variables': {'id': anime_id, 'page': page, 'perpage': perpage}}
		try:
			resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
			resp.raise_for_status()
		except requests.exceptions.HTTPError as e:
			body = e.response.text if getattr(e, 'response', None) is not None else str(e)
			logger.debug('AniList staff query failed: status=%s body=%s', getattr(e.response, 'status_code', None), body)
			raise RuntimeError(body)

		data = resp.json()
		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])

		return data.get('data', {}).get('Media', {}).get('staff', {}).get('edges', [])