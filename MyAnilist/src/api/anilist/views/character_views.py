from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

from src.services.character_service import CharacterService

logger = logging.getLogger(__name__)
service = CharacterService()


@api_view(['GET'])
@permission_classes([AllowAny])
def character_detail(request, character_id):
    """
    Get detailed character information.
    
    This endpoint returns comprehensive character data including:
    - Basic info (name, image, description)
    - All media appearances (anime/manga)
    - Filtered anime appearances
    
    Path parameter:
    - character_id: integer AniList character ID
    
    Response: {
      'id': int,
      'name_full': str,
      'name_native': str,
      'image': str (URL),
      'description': str (HTML formatted),
      'media': [ {id, title_romaji, title_english, cover_image, type, format, status, episodes, season, season_year} ],
      'anime_appearances': [ ...same as media but filtered to ANIME only, limited to 10 ]
    }
    """
    try:
        char_id_val = int(character_id)
    except (TypeError, ValueError):
        return Response({'error': 'character_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        character_data = service.get_character_by_id(char_id_val)
        return Response(character_data, status=status.HTTP_200_OK)
    except LookupError:
        return Response({'error': 'Character not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception('Error fetching character by id: %s', e)
        return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)
