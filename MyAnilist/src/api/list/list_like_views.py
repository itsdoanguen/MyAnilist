from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from src.services.list_like_service import ListLikeService

list_like_service = ListLikeService()
logger = __import__('logging').getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_like_toggle(request, list_id):
    """Toggle like status for a list (like if not liked, unlike if already liked).
    
    Path params:
    - list_id: ID of the list to like/unlike
    
    Response:
    - action: 'liked' or 'unliked'
    - is_liked: current like status after toggle
    - like_count: total number of likes for the list
    
    Permission requirements:
    - User must be authenticated
    - Cannot like private lists that user doesn't have access to
    """
    try:
        auth_user = request.user
        
        result = list_like_service.toggle_list_like(user=auth_user, list_id=list_id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in list_like_toggle: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_like_status(request, list_id):
    """Get like status and count for a list.
    
    Path params:
    - list_id: ID of the list
    
    Response:
    - is_liked: whether the current user has liked this list (false if not authenticated)
    - like_count: total number of likes for the list
    
    Permission:
    - Public endpoint, no authentication required
    - Anonymous users will see is_liked: false
    """
    try:
        auth_user = request.user if request.user.is_authenticated else None
        
        result = list_like_service.get_list_like_status(user=auth_user, list_id=list_id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in list_like_status: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def list_likers_get(request, list_id):
    """Get users who liked a specific list.
    
    Path params:
    - list_id: ID of the list
    
    Body params (JSON):
    - limit: Maximum number of users to return (default: 20, max: 100)
    
    Response:
    - list_id: ID of the list
    - list_name: Name of the list
    - like_count: Total number of likes
    - likers: Array of users who liked this list
    - showing: Number of users being shown
    """
    try:
        data = request.data or {}
        limit = data.get('limit', 20)
        
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return Response({'error': 'limit must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = list_like_service.get_list_likers(list_id=list_id, limit=limit)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in list_likers_get: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def user_liked_lists_get(request):
    """Get all lists that a user has liked.
    
    Body params (JSON):
    - username: Username to get liked lists for (required)
    - limit: Maximum number of lists to return (default: 20, max: 50)
    - offset: Offset for pagination (default: 0)
    
    Response:
    - username: Username of the user
    - total_showing: Number of lists being shown
    - offset: Current offset
    - limit: Current limit
    - liked_lists: Array of lists the user has liked
    
    Permission:
    - Public endpoint
    - Only shows public lists unless viewing own liked lists
    """
    try:
        data = request.data or {}
        username = data.get('username')
        
        if not username:
            return Response({'error': 'username parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        
        try:
            limit = int(limit)
            offset = int(offset)
        except (ValueError, TypeError):
            return Response({'error': 'limit and offset must be integers'}, status=status.HTTP_400_BAD_REQUEST)
        
        requester = request.user if request.user.is_authenticated else None
        
        result = list_like_service.get_user_liked_lists(
            username=username,
            requester=requester,
            limit=limit,
            offset=offset
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in user_liked_lists_get: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def trending_lists_get(request):
    """Get trending lists (recently liked with high activity).
    
    Body params (JSON):
    - limit: Maximum number of lists to return (default: 10, max: 50)
    
    Response:
    - total: Number of trending lists
    - trending_lists: Array of trending lists with like counts and recent activity
    
    Note: Only returns public lists
    """
    try:
        data = request.data or {}
        limit = data.get('limit', 10)
        
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return Response({'error': 'limit must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = list_like_service.get_trending_lists(limit=limit)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception('Error in trending_lists_get: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def most_liked_lists_get(request):
    """Get most liked lists of all time.
    
    Body params (JSON):
    - limit: Maximum number of lists to return (default: 10, max: 50)
    
    Response:
    - total: Number of most liked lists
    - most_liked_lists: Array of most liked lists with like counts
    
    Note: Only returns public lists
    """
    try:
        data = request.data or {}
        limit = data.get('limit', 10)
        
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return Response({'error': 'limit must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = list_like_service.get_most_liked_lists(limit=limit)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception('Error in most_liked_lists_get: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
