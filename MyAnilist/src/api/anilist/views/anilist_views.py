from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

from src.services.anilist_service import AnilistService

logger = logging.getLogger(__name__)
service = AnilistService()


@api_view(['GET'])
@permission_classes([AllowAny])
def anime(request, anime_id):
	"""Retrieve anime information by AniList ID and return basic details plus a short character list.

	Path parameter:
	- anime_id: integer AniList ID

	Response: {
	  'anime': { ... parsed media ... },
	  'characters': [ up to 6 characters, MAIN first then SUPPORTING ]
	}
	"""
	try:
		ani_id_val = int(anime_id)
	except (TypeError, ValueError):
		return Response({'error': 'anime_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	# fetch anime details
	try:
		anime_detail = service.get_by_id(ani_id_val)
	except LookupError:
		return Response({'error': 'Anime not found'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception('Error fetching anime by id: %s', e)
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)

	# fetch a larger character page and then pick up to 6 prioritizing MAIN roles
	try:
		chars = service.get_characters_by_anime_id(ani_id_val, page=1, perpage=20)
	except Exception:
		logger.exception('Error fetching characters for anime id %s', ani_id_val)
		chars = []

	mains = [c for c in chars if (c.get('role') or '').upper() == 'MAIN']
	supporting = [c for c in chars if (c.get('role') or '').upper() != 'MAIN']

	selected = mains[:6]
	if len(selected) < 6:
		need = 6 - len(selected)
		selected.extend(supporting[:need])

	return Response({'anime': anime_detail, 'characters': selected}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def anime_search(request):
	""" 
		Search for anime by criteria. Include Genres, Year, Season, Format, Status
		Season should be one of: SPRING, SUMMER, FALL, WINTER
		Format should be one of: TV_SHOW, TV_SHORT, MOVIE, SPECIAL, OVA, ONA, MUSIC
		Status should be one of: AIRING, FINISHED, NOT_YET_RELEASE, CANCELLED
		Sort should be one of: POPULARITY_DESC, TITLE_ROMAJI, SCORE_DESC, TRENDING_DESC, etc
	"""
	if request.method == 'GET':
		genres = request.query_params.getlist('genres') or None
		year = request.query_params.get('year') or None
		season = request.query_params.get('season') or None
		media_format = request.query_params.get('format') or None
		media_status = request.query_params.get('status') or None
		sort = request.query_params.get('sort') or None
	else:
		body = request.data or {}
		genres = body.get('genres', [])
		year = body.get('year')
		season = body.get('season')
		media_format = body.get('format')
		media_status = body.get('status')
		sort = body.get('sort')

	try:
		try:
			year_val = int(year) if year else None
		except (TypeError, ValueError):
			return Response({'error': 'year must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

		logger.debug('anime_search called with genres=%s year=%s season=%s format=%s status=%s page=%s perpage=%s sort=%s', genres, year_val, season, media_format, media_status, request.query_params.get('page'), request.query_params.get('perpage'), sort)

		results = service.search_by_criteria(genres=genres, year=year_val, season=season, format=media_format, status=media_status, sort=sort)
		return Response(results, status=status.HTTP_200_OK)
	except Exception as e:
		logger.exception(f"Error during anime search: {e}")
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)

@api_view(['POST'])
@permission_classes([AllowAny])
def anime_by_name(request):
	"""POST endpoint that accepts JSON body {"name": "...", "manual": true|false}

	"""
	body = request.data or {}
	name = body.get('name')
	manual = bool(body.get('manual', False))

	if not name:
		return Response({'error': 'Request body must include "name"'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		if manual:
			candidates = service.search_candidates(name, page=1, perpage=10)
			return Response({'candidates': candidates}, status=status.HTTP_200_OK)

		result = service.search_and_get_first(name)
		return Response(result, status=status.HTTP_200_OK)

	except LookupError:
		return Response({'error': 'No search results'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception(f"Unexpected error in anilist.anime_by_name view: {e}")
		return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def trending_anime_by_season(request):
	"""Fetch trending anime from AniList."""

	season = request.query_params.get('season')  # e.g. SPRING, SUMMER, FALL, WINTER
	year = request.query_params.get('year')
	page = request.query_params.get('page')
	perpage = request.query_params.get('perpage')

	# parse ints with fallbacks
	try:
		year_val = int(year) if year else None
	except ValueError:
		return Response({'error': 'year must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		page_val = int(page) if page else 1
	except ValueError:
		return Response({'error': 'page must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		perpage_val = int(perpage) if perpage else 6
	except ValueError:
		return Response({'error': 'perpage must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		trending_anime = service.get_trending_anime_by_season(season=season, season_year=year_val, page=page_val, perpage=perpage_val)
		return Response({'trending': trending_anime}, status=status.HTTP_200_OK)
	except Exception as e:
		logger.exception(f"Error fetching trending anime: {e}")
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)

@api_view(['GET'])
@permission_classes([AllowAny])
def anime_characters(request, anime_id):
	"""Fetch characters for a given anime ID from AniList."""
	try:
		ani_id_val = int(anime_id)
	except ValueError:
		return Response({'error': 'anime_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
	# pagination
	page = request.query_params.get('page')
	perpage = request.query_params.get('perpage')
	language = request.query_params.get('language') or "JAPANESE"

	try:
		page_val = int(page) if page else 1
	except ValueError:
		return Response({'error': 'page must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		perpage_val = int(perpage) if perpage else 10
	except ValueError:
		return Response({'error': 'perpage must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		characters = service.get_characters_by_anime_id(ani_id_val, language=language, page=page_val, perpage=perpage_val)
		return Response({'characters': characters}, status=status.HTTP_200_OK)
	except LookupError:
		return Response({'error': 'Anime not found'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception(f"Error fetching anime characters: {e}")
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)