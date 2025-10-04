from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

from src.services.search_service import SearchService

logger = logging.getLogger(__name__)
service = SearchService()


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def search_by_criteria(request):
	"""
	Search for anime by criteria. Include Genres, Year, Season, Format, Status
	
	Query/Body parameters:
	- genres: list of genre strings
	- year: integer year (optional, defaults to current year)
	- season: SPRING, SUMMER, FALL, WINTER
	- format: TV_SHOW, TV_SHORT, MOVIE, SPECIAL, OVA, ONA, MUSIC
	- status: AIRING, FINISHED, NOT_YET_RELEASE, CANCELLED
	- sort: POPULARITY_DESC, TITLE_ROMAJI, SCORE_DESC, TRENDING_DESC, etc
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

		logger.debug('search_by_criteria called with genres=%s year=%s season=%s format=%s status=%s sort=%s', 
					 genres, year_val, season, media_format, media_status, sort)

		results = service.search_by_criteria(
			genres=genres, 
			year=year_val, 
			season=season, 
			format=media_format, 
			status=media_status, 
			sort=sort
		)
		return Response({'results': results}, status=status.HTTP_200_OK)
	except Exception as e:
		logger.exception(f"Error during anime search: {e}")
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['POST'])
@permission_classes([AllowAny])
def search_by_name(request):
	"""
	POST endpoint that accepts JSON body {"name": "...", "manual": true|false}
	
	- If manual=true: returns list of candidates for user selection
	- If manual=false: returns first match automatically
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
		return Response({'result': result}, status=status.HTTP_200_OK)

	except LookupError:
		return Response({'error': 'No search results'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception(f"Unexpected error in search_by_name view: {e}")
		return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_trending(request):
	"""
	Fetch trending anime for a given season/year from AniList.
	
	Query parameters:
	- season: SPRING, SUMMER, FALL, WINTER (optional, defaults to current)
	- year: integer year (optional, defaults to current)
	- page: integer page number (default: 1)
	- perpage: integer items per page (default: 6)
	"""
	season = request.query_params.get('season')
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
		trending_anime = service.get_trending_anime_by_season(
			season=season, 
			season_year=year_val, 
			page=page_val, 
			perpage=perpage_val
		)
		return Response({'trending': trending_anime}, status=status.HTTP_200_OK)
	except Exception as e:
		logger.exception(f"Error fetching trending anime: {e}")
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)
