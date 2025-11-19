from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from src.services.list_service import ListService
from src.services.user_service import UserService
from .serializers import ListCreateSerializer, ListUpdateSerializer

list_service = ListService()
user_service = UserService()

logger = __import__('logging').getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_create(request):
    """Create a new list for the authenticated user.
    
    Body params:
    - list_name (required): Name of the list
    - description (optional): Description of the list
    - is_private (optional, default=True): Whether the list is private
    - color (optional, default='#3498db'): Hex color code for the list
    """
    try:
        auth_user = request.user
        data = request.data or {}
        
        # Validate input
        serializer = ListCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        
        # Create list
        result = list_service.create_list_for_user(
            user=auth_user,
            list_name=validated['list_name'],
            description=validated.get('description', ''),
            is_private=validated.get('is_private', True),
            color=validated.get('color', '#3498db')
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in list_create: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_lists_get(request):
    """Get all lists for a user.
    
    Query params:
    - username (optional): Username to view lists for. If not provided and user is authenticated,
      shows their own lists. If not provided and not authenticated, returns error.
    
    Permission logic:
    - Viewing own lists: shows all lists (private + public)
    - Viewing other user's lists: shows only public lists
    """
    try:
        username = request.query_params.get('username')
        requester = request.user if request.user.is_authenticated else None
        
        # Determine target user
        if username:
            # View specific user's lists
            target_user = user_service.get_user_by_username(username)
            if not target_user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # No username provided - must be authenticated to view own lists
            if not requester:
                return Response(
                    {'error': 'Authentication required or provide username parameter'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            target_user = requester
        
        # Get lists with proper permissions
        result = list_service.get_user_lists(
            target_user=target_user,
            requester_user=requester
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception('Error in user_lists_get: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def list_update(request, list_id):
    """Update an existing list.
    
    Path params:
    - list_id: ID of the list to update
    
    Body params (all optional):
    - list_name: New name for the list
    - description: New description
    - color: New color (hex format)
    - is_private: New privacy setting (ONLY OWNER can change this)
    
    Permission requirements:
    - User must have can_edit permission on the list
    - Only owner can change is_private field
    """
    try:
        auth_user = request.user
        data = request.data or {}
        
        # Validate input
        serializer = ListUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        
        # Update list with permission checks
        result = list_service.update_list(
            user=auth_user,
            list_id=list_id,
            list_name=validated.get('list_name'),
            description=validated.get('description'),
            color=validated.get('color'),
            is_private=validated.get('is_private')
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in list_update: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_get(request, anilist_id):
    """Get list info for a user and anilist_id.

    Query params: ?username={username} to view another user's list. If not
    provided, uses authenticated user (requires auth).
    """
    return Response({'message': 'list_get not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)