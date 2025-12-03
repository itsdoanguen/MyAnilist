from typing import Dict, Any
from django.core.exceptions import ValidationError

from ..repositories.list_like_repository import ListLikeRepository
from ..repositories.list_repository import ListRepository

logger = __import__('logging').getLogger(__name__)


class ListLikeService:
    """Service for list like operations.

    Responsibilities:
    - toggle like/unlike on lists
    - get like status and count
    - retrieve list likers
    - get user's liked lists
    - get trending and most liked lists
    """

    def __init__(self):
        self.repo = ListLikeRepository()
        self.list_repo = ListRepository()

    def toggle_list_like(self, user, list_id: int) -> Dict[str, Any]:
        """
        Toggle like status for a list (like if not liked, unlike if already liked).

        Args:
            user: User attempting to like/unlike
            list_id: ID of the list

        Returns:
            Dictionary containing action taken and updated like count

        Raises:
            ValidationError: If list not found or not accessible
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')
        
        # Check if list is private - users can only like public lists or lists they have access to
        if lst.isPrivate:
            # Check if user has access to this private list
            user_list = self.list_repo.get_user_list_by_user_and_list(user, list_id)
            if not user_list:
                raise ValidationError('Cannot like a private list you do not have access to')
        
        # Check current like status
        is_liked = self.repo.check_user_liked_list(user, list_id)
        
        if is_liked:
            # Unlike
            deleted = self.repo.delete_list_like(user, list_id)
            action = 'unliked' if deleted else 'no_change'
        else:
            # Like
            like = self.repo.create_list_like(user, list_id)
            action = 'liked' if like else 'no_change'
        
        # Get updated like count
        like_count = self.repo.get_list_likes_count(list_id)
        
        return {
            'list_id': list_id,
            'action': action,
            'is_liked': not is_liked,
            'like_count': like_count,
        }
    
    def get_list_like_status(self, user, list_id: int) -> Dict[str, Any]:
        """
        Get like status and count for a list.

        Args:
            user: User checking the status (can be None for anonymous)
            list_id: ID of the list

        Returns:
            Dictionary containing like status and count

        Raises:
            ValidationError: If list not found
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')
        
        # Check if user has liked (only if user is authenticated)
        is_liked = False
        if user and user.is_authenticated:
            is_liked = self.repo.check_user_liked_list(user, list_id)
        
        # Get like count
        like_count = self.repo.get_list_likes_count(list_id)
        
        return {
            'list_id': list_id,
            'is_liked': is_liked,
            'like_count': like_count,
        }
    
    def get_list_likers(self, list_id: int, limit: int = 20) -> Dict[str, Any]:
        """
        Get users who liked a list.

        Args:
            list_id: ID of the list
            limit: Maximum number of users to return (default: 20, max: 100)

        Returns:
            Dictionary containing list info and users who liked it

        Raises:
            ValidationError: If list not found
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')
        
        # Validate limit
        limit = min(max(1, limit), 100)
        
        # Get users who liked
        likers = self.repo.get_list_likers(list_id, limit=limit)
        
        # Format response
        users = []
        for user in likers:
            users.append({
                'id': user.id,
                'username': user.username,
                'email_verified': getattr(user, 'email_verified', False),
            })
        
        # Get total like count
        like_count = self.repo.get_list_likes_count(list_id)
        
        return {
            'list_id': list_id,
            'list_name': lst.list_name,
            'like_count': like_count,
            'likers': users,
            'showing': len(users),
        }
    
    def get_user_liked_lists(self, username: str, requester=None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Get all lists that a user has liked.

        Args:
            username: Username to get liked lists for
            requester: User making the request (for privacy filtering)
            limit: Maximum number of lists to return
            offset: Offset for pagination

        Returns:
            Dictionary containing user info and their liked lists

        Raises:
            ValidationError: If user not found
        """
        from src.services.user_service import UserService
        
        user_service = UserService()
        target_user = user_service.get_user_by_username(username)
        
        if not target_user:
            raise ValidationError('User not found')
        
        # Validate pagination params
        limit = min(max(1, limit), 50)
        offset = max(0, offset)
        
        # Get liked lists
        liked_list_objects = self.repo.get_user_liked_lists(target_user, limit=limit, offset=offset)
        
        # Check if requester is viewing their own liked lists
        is_own = requester and requester.pk == target_user.pk
        
        # Format response with privacy filtering
        lists = []
        for list_like in liked_list_objects:
            lst = list_like.list
            
            # Privacy check: skip private lists if not viewing own or not a member
            if lst.isPrivate and not is_own:
                user_list = self.list_repo.get_user_list_by_user_and_list(requester, lst.list_id) if requester else None
                if not user_list:
                    continue
            
            lists.append({
                'list_id': lst.list_id,
                'list_name': lst.list_name,
                'description': lst.description,
                'is_private': lst.isPrivate,
                'color': lst.color,
                'created_at': lst.created_at.isoformat() if lst.created_at else None,
                'liked_at': list_like.liked_at.isoformat() if list_like.liked_at else None,
                'like_count': self.repo.get_list_likes_count(lst.list_id),
            })
        
        return {
            'username': username,
            'total_showing': len(lists),
            'offset': offset,
            'limit': limit,
            'liked_lists': lists,
        }
    
    def get_trending_lists(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get trending lists (recently liked with high activity).

        Args:
            limit: Maximum number of lists to return

        Returns:
            Dictionary containing trending lists
        """
        limit = min(max(1, limit), 50)
        
        recent_liked = self.repo.get_recent_liked_lists(limit=limit * 2)  # Get more to filter
        
        # Get full list details
        trending = []
        for item in recent_liked:
            lst = self.list_repo.get_details_of_list(item['list_id'])
            if lst and not lst.isPrivate:  # Only include public lists
                trending.append({
                    'list_id': lst.list_id,
                    'list_name': lst.list_name,
                    'description': lst.description,
                    'color': lst.color,
                    'like_count': item['like_count'],
                    'recent_liked_at': item['recent_liked_at'].isoformat() if item['recent_liked_at'] else None,
                })
                
                if len(trending) >= limit:
                    break
        
        return {
            'total': len(trending),
            'trending_lists': trending,
        }
    
    def get_most_liked_lists(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get most liked lists of all time with owner info and anime preview.

        Args:
            limit: Maximum number of lists to return

        Returns:
            Dictionary containing most liked lists with extended data
        """
        from src.services.anime_service import AnimeService
        
        limit = min(max(1, limit), 50)
        
        most_liked = self.repo.get_most_liked_lists(limit=limit * 2)  # Get more to filter
        
        all_anime_ids = []
        for item in most_liked:
            if item['list'] and not item['list'].isPrivate:
                all_anime_ids.extend([anime.anilist_id for anime in item['preview_anime']])
        
        anime_service = AnimeService()
        anime_covers = anime_service.get_anime_covers(all_anime_ids) if all_anime_ids else {}
        
        top_lists = []
        for item in most_liked:
            lst = item['list']
            if lst and not lst.isPrivate:  
                owner = item['owner']
                
                list_data = {
                    'list_id': lst.list_id,
                    'list_name': lst.list_name,
                    'description': lst.description,
                    'color': lst.color,
                    'like_count': item['like_count'],
                    'anime_count': item['anime_count'],
                    'owner': {
                        'username': owner.username if owner else None,
                        'avatar_url': owner.avatar_url if owner and hasattr(owner, 'avatar_url') else None,
                    },
                    'preview_anime': [
                        {
                            'anilist_id': anime.anilist_id,
                            'cover_image': anime_covers.get(anime.anilist_id),
                        }
                        for anime in item['preview_anime']
                    ]
                }
                
                top_lists.append(list_data)
                
                if len(top_lists) >= limit:
                    break
        
        return {
            'total': len(top_lists),
            'most_liked_lists': top_lists,
        }
