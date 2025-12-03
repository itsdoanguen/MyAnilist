from typing import List


class ListLikeRepository:
    """
    Repository for ListLike DB operations.
    """

    @staticmethod
    def check_user_liked_list(user, list_id: int) -> bool:
        """
        Check if a user has liked a list.

        Args:
            user: User instance
            list_id: ID of the list

        Returns:
            True if user has liked the list, False otherwise
        """
        from src.models.list_like import ListLike

        return ListLike.objects.filter(user=user, list_id=list_id).exists()
    
    @staticmethod
    def create_list_like(user, list_id: int):
        """
        Create a like for a list.

        Args:
            user: User instance
            list_id: ID of the list

        Returns:
            ListLike instance if created, None if already exists
        """
        from src.models.list_like import ListLike
        from django.db import IntegrityError

        try:
            like = ListLike.objects.create(user=user, list_id=list_id)
            return like
        except IntegrityError:
            # Already liked
            return None
    
    @staticmethod
    def delete_list_like(user, list_id: int) -> bool:
        """
        Remove a like from a list.

        Args:
            user: User instance
            list_id: ID of the list

        Returns:
            True if deleted, False if like didn't exist
        """
        from src.models.list_like import ListLike

        deleted_count, _ = ListLike.objects.filter(user=user, list_id=list_id).delete()
        return deleted_count > 0
    
    @staticmethod
    def get_list_likes_count(list_id: int) -> int:
        """
        Get the total number of likes for a list.

        Args:
            list_id: ID of the list

        Returns:
            Number of likes
        """
        from src.models.list_like import ListLike

        return ListLike.objects.filter(list_id=list_id).count()
    
    @staticmethod
    def get_list_likers(list_id: int, limit: int = 10):
        """
        Get users who liked a list.

        Args:
            list_id: ID of the list
            limit: Maximum number of users to return

        Returns:
            List of User instances
        """
        from src.models.list_like import ListLike

        likes = ListLike.objects.filter(list_id=list_id).select_related('user').order_by('-liked_at')[:limit]
        return [like.user for like in likes]
    
    @staticmethod
    def get_user_liked_lists(user, limit: int = None, offset: int = 0):
        """
        Get all lists that a user has liked.

        Args:
            user: User instance
            limit: Maximum number of lists to return (None for all)
            offset: Offset for pagination

        Returns:
            QuerySet of ListLike instances with related List
        """
        from src.models.list_like import ListLike

        qs = ListLike.objects.filter(user=user).select_related('list').order_by('-liked_at')
        
        if limit is not None:
            qs = qs[offset:offset + limit]
        
        return list(qs)
    
    @staticmethod
    def get_recent_liked_lists(limit: int = 10):
        """
        Get recently liked lists across all users.
        If not enough lists with likes, includes recent public lists without likes.

        Args:
            limit: Maximum number of lists to return

        Returns:
            List of dicts with list_id, like_count, recent_liked_at
        """
        from src.models.list_like import ListLike
        from src.models.list import List
        from django.db.models import Count, Max

        # Get lists with likes, ordered by most recent like
        recent_likes = (
            ListLike.objects
            .values('list_id')
            .annotate(
                like_count=Count('id'),
                recent_liked_at=Max('liked_at')
            )
            .order_by('-recent_liked_at')[:limit * 2]  # Get more to ensure enough after filtering
        )
        
        result = list(recent_likes)
        
        # If not enough, add recent public lists without likes
        if len(result) < limit:
            liked_list_ids = [item['list_id'] for item in result]
            remaining = limit - len(result)
            
            # Get recent public lists that haven't been liked
            additional_lists = (
                List.objects
                .filter(isPrivate=False)
                .exclude(list_id__in=liked_list_ids)
                .order_by('-created_at')[:remaining]
            )
            
            for lst in additional_lists:
                result.append({
                    'list_id': lst.list_id,
                    'like_count': 0,
                    'recent_liked_at': None
                })
        
        return result[:limit]
    
    @staticmethod
    def get_most_liked_lists(limit: int = 10):
        """
        Get most liked lists with owner info and anime preview.
        If not enough lists with likes, includes recent public lists without likes.

        Args:
            limit: Maximum number of lists to return

        Returns:
            List of dicts with list_id, like_count, owner info, anime_count, and preview_anime
        """
        from src.models.list_like import ListLike
        from src.models.list import List, UserList, AnimeList
        from django.db.models import Count

        most_liked = (
            ListLike.objects
            .values('list_id')
            .annotate(like_count=Count('id'))
            .order_by('-like_count')[:limit * 2]  # Get more to ensure enough after filtering
        )
        
        result = []
        for item in most_liked:
            list_id = item['list_id']
            
            # Get list details
            try:
                lst = List.objects.get(list_id=list_id)
            except List.DoesNotExist:
                continue
            
            # Get owner info
            owner_user_list = UserList.objects.filter(list_id=list_id, is_owner=True).select_related('user').first()
            owner = owner_user_list.user if owner_user_list else None
            
            # Get anime count
            anime_count = AnimeList.objects.filter(list_id=list_id).count()
            
            # Get first 3 anime for preview
            preview_anime = AnimeList.objects.filter(list_id=list_id).order_by('-added_date')[:3]
            
            result.append({
                'list_id': list_id,
                'list': lst,
                'like_count': item['like_count'],
                'owner': owner,
                'anime_count': anime_count,
                'preview_anime': list(preview_anime)
            })
        
        # If not enough, add recent public lists without likes
        if len(result) < limit:
            liked_list_ids = [item['list_id'] for item in result]
            remaining = limit - len(result)
            
            # Get recent public lists that haven't been liked
            additional_lists = (
                List.objects
                .filter(isPrivate=False)
                .exclude(list_id__in=liked_list_ids)
                .order_by('-created_at')[:remaining]
            )
            
            for lst in additional_lists:
                # Get owner info
                owner_user_list = UserList.objects.filter(list_id=lst.list_id, is_owner=True).select_related('user').first()
                owner = owner_user_list.user if owner_user_list else None
                
                # Get anime count
                anime_count = AnimeList.objects.filter(list_id=lst.list_id).count()
                
                # Get first 3 anime for preview
                preview_anime = AnimeList.objects.filter(list_id=lst.list_id).order_by('-added_date')[:3]
                
                result.append({
                    'list_id': lst.list_id,
                    'list': lst,
                    'like_count': 0,
                    'owner': owner,
                    'anime_count': anime_count,
                    'preview_anime': list(preview_anime)
                })
        
        return result[:limit]
