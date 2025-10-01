import requests
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class AnilistRepository:
	"""Repository responsible for making HTTP requests to the AniList GraphQL API
	and returning raw media dictionaries (no transformation).
	"""
	ANILIST_ENDPOINT = 'https://graphql.anilist.co'

	ANIME_INFO_QS = '''
	query ($id: Int) {
		Media(id: $id, type: ANIME) {
			id
			title { romaji english }
			startDate { year month day }
			endDate { year month day }
			coverImage { large }
			bannerImage
			format
			status
			episodes
			season
			description
			averageScore
			genres
			nextAiringEpisode { airingAt timeUntilAiring episode }
		}
	}
	'''

	ANIME_ID_SEARCH_QS = '''
	query ($query: String, $page: Int, $perpage: Int) {
		Page (page: $page, perPage: $perpage) {
			pageInfo { total currentPage lastPage hasNextPage }
			media (search: $query, type: ANIME) {
				id
				title { romaji english }
				coverImage { large }
				averageScore
				popularity
				episodes
				season
				isAdult
			}
		}
	}
	'''

	def fetch_anime_by_id(self, anime_id: int) -> Optional[dict]:
		payload = {'query': self.ANIME_INFO_QS, 'variables': {'id': anime_id}}
		resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
		resp.raise_for_status()
		data = resp.json()
		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])
		return data.get('data', {}).get('Media')

	def search_media(self, query: str, page: int = 1, perpage: int = 10) -> List[dict]:
		payload = {'query': self.ANIME_ID_SEARCH_QS, 'variables': {'query': query, 'page': page, 'perpage': perpage}}
		resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
		resp.raise_for_status()
		data = resp.json()
		if 'errors' in data:
			logger.debug('AniList returned errors: %s', data['errors'])
			raise RuntimeError(data['errors'])
		return data.get('data', {}).get('Page', {}).get('media', [])


