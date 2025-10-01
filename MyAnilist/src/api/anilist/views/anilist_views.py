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
def anime(request):
	"""Retrieve anime information from AniList GraphQL API.

	Query parameters:
	- id: integer AniList ID (preferred)
	- q: search string to lookup by name
	- manual: if 'true' and using search, return list of candidates instead of selecting first

	Example responses (JSON):

	1) GET by id (success)
	{
		"id": 9253,
		"name_romaji": "Kimi no Na wa.",
		"name_english": "Your Name.",
		"starting_time": "8/26/2016",
		"ending_time": "10/1/2016",
		"cover_image": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx9253-abc123.jpg",
		"banner_image": "https://s4.anilist.co/file/anilistcdn/media/anime/banner/9253.jpg",
		"airing_format": "MOVIE",
		"airing_status": "FINISHED",
		"airing_episodes": 1,
		"season": "SUMMER",
		"desc": "A brief HTML/Markdown description...",
		"average_score": 88,
		"genres": ["Romance", "Supernatural"],
		"next_airing_ep": null
	}

	2) GET by search (auto-select first result)
	{
		"id": 20,
		"name_romaji": "Naruto",
		"name_english": null,
		"starting_time": "10/3/2002",
		"ending_time": "2/8/2007",
		"cover_image": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx20.jpg",
		"banner_image": null,
		"airing_format": "TV",
		"airing_status": "FINISHED",
		"airing_episodes": 220,
		"season": "FALL",
		"desc": "Long description...",
		"average_score": 72,
		"genres": ["Action", "Adventure"],
		"next_airing_ep": null
	}

	3) GET by search (manual=true) returns candidates list
	{
		"candidates": [
			{"id": 20, "romaji": "Naruto", "english": null, "cover": "...", "average_score": 72, "episodes": 220, "season": "FALL"},
			{"id": 1735, "romaji": "Naruto: Shippuuden", "english": null, "cover": "...", "average_score": 78, "episodes": 500, "season": "WINTER"}
		]
	}
	"""
	ani_id = request.query_params.get('id')
	q = request.query_params.get('q')
	manual = request.query_params.get('manual', 'false').lower() == 'true'

	try:
		if ani_id:
			try:
				ani_id_val = int(ani_id)
			except ValueError:
				return Response({'error': 'id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

			try:
				result = service.get_by_id(ani_id_val)
				return Response(result, status=status.HTTP_200_OK)
			except LookupError:
				return Response({'error': 'Anime not found'}, status=status.HTTP_404_NOT_FOUND)
			except Exception as e:
				logger.exception('Error fetching anime by id: %s', e)
				return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)

		elif q:
			try:
				if manual:
					candidates = service.search_candidates(q, page=1, perpage=10)
					return Response({'candidates': candidates}, status=status.HTTP_200_OK)
				result = service.search_and_get_first(q)
				return Response(result, status=status.HTTP_200_OK)
			except LookupError:
				return Response({'error': 'No search results'}, status=status.HTTP_404_NOT_FOUND)
			except Exception as e:
				logger.exception('Error during search: %s', e)
				return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)

		else:
			return Response({'error': 'Provide either id or q (search) parameter'}, status=status.HTTP_400_BAD_REQUEST)

	except Exception as e:
		logger.exception(f"Unexpected error in anilist.anime view: {e}")
		return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def anime_by_name(request):
	"""POST endpoint that accepts JSON body {"name": "...", "manual": true|false}

	Returns the same payloads as the GET search flow. This is convenient for clients that prefer
	sending POST bodies rather than query params.
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

