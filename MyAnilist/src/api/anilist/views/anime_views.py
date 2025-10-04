from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

from src.services.anime_service import AnimeService

logger = logging.getLogger(__name__)
service = AnimeService()


@api_view(['GET'])
@permission_classes([AllowAny])
def anime_detail(request, anime_id):
	"""
	Get basic anime information (for sidebar/header).
	
	This lightweight endpoint returns only essential anime data without any
	related entities (characters, staff, etc.). Use this to populate the
	sidebar/header that persists across all tabs.

	Path parameter:
	- anime_id: integer AniList ID

	Response: {
	  'id', 'name_romaji', 'name_english', 'cover_image', 'banner_image',
	  'airing_format', 'airing_status', 'airing_episodes', 'average_score',
	  'popularity', 'genres', 'season', 'season_year', etc.
	}
	"""
	try:
		ani_id_val = int(anime_id)
	except (TypeError, ValueError):
		return Response({'error': 'anime_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		anime_data = service.get_by_id(ani_id_val)
		return Response(anime_data, status=status.HTTP_200_OK)
	except LookupError:
		return Response({'error': 'Anime not found'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception('Error fetching anime by id: %s', e)
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
@permission_classes([AllowAny])
def anime_overview(request, anime_id):
	"""
	Get overview tab content with characters and staff preview.
	
	This endpoint returns ONLY preview data of characters/staff/etc for the Overview tab.

	Path parameter:
	- anime_id: integer AniList ID

	Response: {
	  'characters': [ {id, name_full, image, role, voice_actor} ] (up to 6, MAIN prioritized),
	  'staff': [ {id, name_full, image, role} ] (up to 3, important roles prioritized)
	}
	"""
	try:
		ani_id_val = int(anime_id)
	except (TypeError, ValueError):
		return Response({'error': 'anime_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		overview_data = service.get_overview_data(ani_id_val)
		return Response(overview_data, status=status.HTTP_200_OK)
	except LookupError:
		return Response({'error': 'Anime not found'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception('Error fetching anime overview: %s', e)
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
@permission_classes([AllowAny])
def anime_characters(request, anime_id):
	"""
	Fetch characters for a given anime ID (for Characters tab).
	
	Path parameter:
	- anime_id: integer AniList ID
	
	Query parameters:
	- page: integer page number (default: 1)
	- perpage: integer items per page (default: 10)
	- language: voice actor language filter (default: JAPANESE)
	
	Response: {
	  'characters': [ {id, name_full, image, role, voice_actors: [...]} ]
	}
	"""
	try:
		ani_id_val = int(anime_id)
	except (TypeError, ValueError):
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
	except Exception as e:
		logger.exception(f"Error fetching anime characters: {e}")
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
@permission_classes([AllowAny])
def anime_staff(request, anime_id):
	"""
	Fetch staff for a given anime ID (for Staff tab).
	
	Path parameter:
	- anime_id: integer AniList ID
	
	Query parameters:
	- page: integer page number (default: 1)
	- perpage: integer items per page (default: 10)
	
	Response: {
	  'staff': [ {id, name_full, name_native, image, role} ]
	}
	"""
	try:
		ani_id_val = int(anime_id)
	except (TypeError, ValueError):
		return Response({'error': 'anime_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	# pagination
	page = request.query_params.get('page')
	perpage = request.query_params.get('perpage')

	try:
		page_val = int(page) if page else 1
	except ValueError:
		return Response({'error': 'page must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		perpage_val = int(perpage) if perpage else 10
	except ValueError:
		return Response({'error': 'perpage must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		staff = service.get_staff_by_anime_id(ani_id_val, page=page_val, perpage=perpage_val)
		return Response({'staff': staff}, status=status.HTTP_200_OK)
	except Exception as e:
		logger.exception(f"Error fetching anime staff: {e}")
		return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)

