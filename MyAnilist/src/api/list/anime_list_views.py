from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError

from src.services.anime_list_service import AnimeListService
from .anime_serializers import AnimeAddSerializer, AnimeNoteUpdateSerializer

anime_list_service = AnimeListService()

logger = __import__('logging').getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def anime_add(request, list_id):
    """Add an anime to a list.
    
    Path params:
    - list_id: ID of the list
    
    Body params:
    - anilist_id (required): AniList anime ID
    - note (optional): Note about the anime
    
    Permission requirements:
    - User must be a member of the list with can_edit permission
    
    Example request:
    POST /api/list/anime/1/add/
    {
        "anilist_id": 21,
        "note": "One of the best anime ever"
    }
    """
    try:
        user = request.user
        
        try:
            data = request.data
        except Exception as parse_error:
            logger.warning(f'Failed to parse request data: {parse_error}')
            data = {}
        
        data = data or {}
        
        # Validate input
        serializer = AnimeAddSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        
        # Add anime to list
        result = anime_list_service.add_anime_to_list(
            user=user,
            list_id=list_id,
            anilist_id=validated['anilist_id'],
            note=validated.get('note', '')
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except DRFValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in anime_add: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def anime_list_get(request, list_id):
    """Get all anime in a list.
    
    Path params:
    - list_id: ID of the list
    
    Permission requirements:
    - Public lists: anyone can view
    - Private lists: only members can view
    
    Example: GET /api/list/anime/1/
    """
    try:
        user = request.user if request.user.is_authenticated else None
        
        # Get anime list
        result = anime_list_service.get_anime_list(
            user=user,
            list_id=list_id
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in anime_list_get: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def anime_note_update(request, list_id, anilist_id):
    """Update the note for an anime in a list.
    
    Path params:
    - list_id: ID of the list
    - anilist_id: AniList anime ID
    
    Body params:
    - note (required): New note content (can be empty string)
    
    Permission requirements:
    - User must be a member of the list with can_edit permission
    
    Example request:
    PUT /api/list/anime/1/21/update/
    {
        "note": "Updated note about this anime"
    }
    """
    try:
        user = request.user
        
        try:
            data = request.data
        except Exception as parse_error:
            logger.warning(f'Failed to parse request data: {parse_error}')
            data = {}
        
        data = data or {}
        
        # Validate input
        serializer = AnimeNoteUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        
        # Update anime note
        result = anime_list_service.update_anime_note(
            user=user,
            list_id=list_id,
            anilist_id=anilist_id,
            note=validated['note']
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except DRFValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in anime_note_update: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def anime_remove(request, list_id, anilist_id):
    """Remove an anime from a list.
    
    Path params:
    - list_id: ID of the list
    - anilist_id: AniList anime ID
    
    Permission requirements:
    - User must be a member of the list with can_edit permission
    
    Example: DELETE /api/list/anime/1/21/remove/
    """
    try:
        user = request.user
        
        # Remove anime from list
        result = anime_list_service.remove_anime_from_list(
            user=user,
            list_id=list_id,
            anilist_id=anilist_id
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in anime_remove: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
