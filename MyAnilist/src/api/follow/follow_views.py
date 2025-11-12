from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from src.services.user_service import UserService
from src.services.anime_follow_service import AnimeFollowService
from .serializers import FollowSerializer

user_service = UserService()
follow_service = AnimeFollowService()


@api_view(['GET'])
@permission_classes([AllowAny])
def follow_get(request, anilist_id):
    """Get follow info for a user and anilist_id.

    Query params: ?username={username} to view another user's follow. If not
    provided, uses authenticated user (requires auth).
    """
    try:
        username = request.query_params.get('username')
        target_user = None
        if username:
            target_user = user_service.get_user_by_username(username)
            if not target_user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            if request.user and request.user.is_authenticated:
                target_user = request.user
            else:
                return Response({'error': 'username query param required for anonymous requests'}, status=status.HTTP_400_BAD_REQUEST)

        follow = follow_service.get_follow(target_user, anilist_id)
        if not follow:
            default_payload = {
                "anilist_id": int(anilist_id),
                "notify_email": False,
                "episode_progress": 0,
                "watch_status": "plan_to_watch",
                "isFavorite": False,
                "start_date": None,
                "finish_date": None,
                "total_rewatch": 0,
                "user_note": "",
                "created_at": None,
                "updated_at": None,
                "is_following": False,
            }
            return Response(default_payload, status=status.HTTP_200_OK)

        payload = {
            "anilist_id": follow.anilist_id,
            "notify_email": follow.notify_email,
            "episode_progress": follow.episode_progress,
            "watch_status": follow.watch_status,
            "isFavorite": follow.isFavorite,
            "start_date": follow.start_date.isoformat() if follow.start_date else None,
            "finish_date": follow.finish_date.isoformat() if follow.finish_date else None,
            "total_rewatch": follow.total_rewatch,
            "user_note": follow.user_note,
            "created_at": follow.created_at.isoformat() if follow.created_at else None,
            "updated_at": follow.updated_at.isoformat() if follow.updated_at else None,
            "is_following": True,
        }

        return Response(payload, status=status.HTTP_200_OK)
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('Error in follow_get: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_create(request, anilist_id):
    """Create a follow for the authenticated user."""
    try:
        auth_user = request.user
        data = request.data or {}
        serializer = FollowSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        if 'notify_email' in validated:
            validated['notify_email'] = auth_user.email if validated['notify_email'] else ''

        follow = follow_service.create_or_update_follow(auth_user, anilist_id, **validated)
        payload = {
            "anilist_id": follow.anilist_id,
            "notify_email": follow.notify_email,
            "episode_progress": follow.episode_progress,
            "watch_status": follow.watch_status,
            "isFavorite": follow.isFavorite,
            "start_date": follow.start_date.isoformat() if follow.start_date else None,
            "finish_date": follow.finish_date.isoformat() if follow.finish_date else None,
            "total_rewatch": follow.total_rewatch,
            "user_note": follow.user_note,
            "created_at": follow.created_at.isoformat() if follow.created_at else None,
            "updated_at": follow.updated_at.isoformat() if follow.updated_at else None,
            "is_following": True,
        }

        try:
            user_service.create_activity(auth_user, 'followed_anime', 'AnimeFollow', follow.anilist_id, {}, is_public=True)
        except Exception:
            return Response({'error': 'Error when logging activity'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(payload, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('Error in follow_create: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def follow_update(request, anilist_id):
    """Update an existing follow for the authenticated user."""
    try:
        auth_user = request.user
        data = request.data or {}
        serializer = FollowSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        if 'notify_email' in validated:
            validated['notify_email'] = auth_user.email if validated['notify_email'] else ''

        follow = follow_service.create_or_update_follow(auth_user, anilist_id, **validated)
        payload = {
            "anilist_id": follow.anilist_id,
            "notify_email": follow.notify_email,
            "episode_progress": follow.episode_progress,
            "watch_status": follow.watch_status,
            "isFavorite": follow.isFavorite,
            "start_date": follow.start_date.isoformat() if follow.start_date else None,
            "finish_date": follow.finish_date.isoformat() if follow.finish_date else None,
            "total_rewatch": follow.total_rewatch,
            "user_note": follow.user_note,
            "created_at": follow.created_at.isoformat() if follow.created_at else None,
            "updated_at": follow.updated_at.isoformat() if follow.updated_at else None,
            "is_following": True,
        }

        try: 
            user_service.create_activity(auth_user, 'updated_followed_anime', 'AnimeFollow', follow.anilist_id, {}, is_public=True)
        except Exception:
            return Response({'error': 'Error when logging activity'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(payload, status=status.HTTP_200_OK)
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('Error in follow_update: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def follow_delete(request, anilist_id):
    """Delete follow for authenticated user."""
    try:
        auth_user = request.user
        deleted = follow_service.remove_follow(auth_user, anilist_id)
        return Response({'deleted': bool(deleted)}, status=status.HTTP_200_OK)
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('Error in follow_delete: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_502_BAD_GATEWAY)
