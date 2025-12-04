from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
import logging

from src.services.anime_notification_service import AnimeNotificationService

logger = logging.getLogger(__name__)

notification_service = AnimeNotificationService()


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_preferences(request):
    """
    Get or update user's anime notification preferences.
    
    GET: Returns current preferences
    PUT: Updates preferences
    
    Request body for PUT:
    {
        "notify_before_hours": 24,
        "enabled": true,
        "notify_by_email": true,
        "notify_in_app": true
    }
    """
    try:
        if request.method == 'GET':
            preferences = notification_service.get_user_preference(request.user)
            return Response(preferences, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            data = request.data
            
            # Validate notify_before_hours
            notify_before_hours = data.get('notify_before_hours')
            if notify_before_hours is not None:
                if not isinstance(notify_before_hours, int) or notify_before_hours < 1 or notify_before_hours > 168:
                    return Response(
                        {'error': 'notify_before_hours must be between 1 and 168 (1 week)'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Update preferences
            update_data = {}
            if 'notify_before_hours' in data:
                update_data['notify_before_hours'] = data['notify_before_hours']
            if 'enabled' in data:
                update_data['enabled'] = bool(data['enabled'])
            if 'notify_by_email' in data:
                update_data['notify_by_email'] = bool(data['notify_by_email'])
            if 'notify_in_app' in data:
                update_data['notify_in_app'] = bool(data['notify_in_app'])
            
            preferences = notification_service.update_user_preference(request.user, **update_data)
            
            return Response({
                'message': 'Preferences updated successfully',
                'preferences': preferences
            }, status=status.HTTP_200_OK)
    
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Error in notification_preferences: {e}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_notifications(request):
    """
    Get user's scheduled anime airing notifications.
    
    Query params:
    - status: Filter by status (pending, sent, failed, cancelled)
    - limit: Maximum number to return (default 50)
    """
    try:
        status_filter = request.GET.get('status', None)
        limit = int(request.GET.get('limit', 50))
        
        if limit < 1 or limit > 200:
            return Response(
                {'error': 'limit must be between 1 and 200'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = notification_service.get_user_notifications(
            request.user,
            status=status_filter,
            limit=limit
        )
        
        return Response({
            'notifications': notifications,
            'count': len(notifications)
        }, status=status.HTTP_200_OK)
    
    except ValueError:
        return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Error in my_notifications: {e}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_anime_notifications(request, anilist_id):
    """
    Cancel all pending notifications for a specific anime.
    
    Path param:
    - anilist_id: AniList anime ID
    """
    try:
        result = notification_service.cancel_notifications_for_anime(request.user, anilist_id)
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.exception(f"Error in cancel_anime_notifications: {e}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
