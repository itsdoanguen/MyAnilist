from typing import List

class ListRepository:
    """
    Repository for List DB operations.
    """

    @staticmethod
    def get_lists_of_user(user) -> List:
        """
        Return a list of UserList model instances for the given user.

        Ordered by created_at descending (most recent first).
        """
        from src.models.list import UserList

        qs = UserList.objects.filter(user=user).order_by('-created_at')
        return list(qs)
    
    @staticmethod
    def get_details_of_list(list_id: int):
        """
        Return the List instance for the given list_id.

        Returns None if not found.
        """
        from src.models.list import List

        try:
            lst = List.objects.get(list_id=list_id)
            return lst
        except List.DoesNotExist:
            return None
    
    @staticmethod
    def create_list(list_name: str, description: str = '', is_private: bool = True, color: str = '#3498db'):
        """
        Create a new List instance.

        Returns the created List instance.
        """
        from src.models.list import List

        new_list = List.objects.create(
            list_name=list_name,
            description=description,
            isPrivate=is_private,
            color=color
        )
        return new_list
    
    @staticmethod
    def create_user_list(user, list_obj, is_owner: bool = True, can_edit: bool = True):
        """
        Create a UserList entry linking a user to a list.

        Returns the created UserList instance.
        """
        from src.models.list import UserList

        user_list = UserList.objects.create(
            user=user,
            list=list_obj,
            is_owner=is_owner,
            can_edit=can_edit
        )
        return user_list
    
    @staticmethod
    def get_user_list_by_user_and_list(user, list_id: int):
        """
        Return the UserList instance for a given user and list_id.

        Returns None if not found.
        """
        from src.models.list import UserList

        try:
            return UserList.objects.get(user=user, list_id=list_id)
        except UserList.DoesNotExist:
            return None
    
    @staticmethod
    def get_lists_with_details(user, include_private: bool = False) -> List:
        """
        Get all lists for a user with full List details.

        Args:
            user: User instance to get lists for
            include_private: If True, include private lists. If False, only public lists.

        Returns:
            List of dictionaries containing UserList and List details
        """
        from src.models.list import UserList

        qs = UserList.objects.filter(user=user).select_related('list').order_by('-list__created_at')
        
        if not include_private:
            qs = qs.filter(list__isPrivate=False)
        
        results = []
        for user_list in qs:
            results.append({
                'user_list': user_list,
                'list': user_list.list
            })
        
        return results
    
    @staticmethod
    def update_list(list_id: int, **kwargs):
        """
        Update a List instance with the provided fields.

        Args:
            list_id: ID of the list to update
            **kwargs: Fields to update (list_name, description, color, isPrivate)

        Returns:
            Updated List instance or None if not found
        """
        from src.models.list import List

        try:
            lst = List.objects.get(list_id=list_id)
            for key, value in kwargs.items():
                if hasattr(lst, key):
                    setattr(lst, key, value)
            lst.save()
            return lst
        except List.DoesNotExist:
            return None
    
    @staticmethod
    def check_user_is_owner(user, list_id: int) -> bool:
        """
        Check if a user is the owner of a list.

        Returns:
            True if user is owner, False otherwise
        """
        from src.models.list import UserList

        try:
            user_list = UserList.objects.get(user=user, list_id=list_id)
            return user_list.is_owner
        except UserList.DoesNotExist:
            return False
    
    @staticmethod
    def check_user_can_edit(user, list_id: int) -> bool:
        """
        Check if a user can edit a list (has can_edit permission).

        Returns:
            True if user can edit, False otherwise
        """
        from src.models.list import UserList

        try:
            user_list = UserList.objects.get(user=user, list_id=list_id)
            return user_list.can_edit
        except UserList.DoesNotExist:
            return False
    
    @staticmethod
    def delete_list(list_id: int) -> bool:
        """
        Delete a List instance and all related records.

        Args:
            list_id: ID of the list to delete

        Returns:
            True if deleted successfully, False if not found
        """
        from src.models.list import List

        try:
            lst = List.objects.get(list_id=list_id)
            lst.delete()
            return True
        except List.DoesNotExist:
            return False
    
    @staticmethod
    def get_anime_items_in_list(list_id: int):
        """
        Get all anime items in a list.

        Args:
            list_id: ID of the list

        Returns:
            QuerySet of AnimeList instances
        """
        from src.models.list import AnimeList

        return AnimeList.objects.filter(list_id=list_id).order_by('added_date')
    
    @staticmethod
    def copy_anime_to_list(source_list_id: int, target_list_id: int, user):
        """
        Copy all anime items from source list to target list.

        Args:
            source_list_id: ID of the source list
            target_list_id: ID of the target list
            user: User who is copying (will be set as added_by)

        Returns:
            Number of anime items copied
        """
        from src.models.list import AnimeList

        # Get all anime from source list
        source_anime = AnimeList.objects.filter(list_id=source_list_id)
        
        # Create copies in target list
        copied_count = 0
        for anime in source_anime:
            # Check if anime already exists in target list
            exists = AnimeList.objects.filter(
                list_id=target_list_id,
                anilist_id=anime.anilist_id
            ).exists()
            
            if not exists:
                AnimeList.objects.create(
                    list_id=target_list_id,
                    anilist_id=anime.anilist_id,
                    added_by=user,
                    note=anime.note  # Copy note from original
                )
                copied_count += 1
        
        return copied_count
    
    @staticmethod
    def get_public_lists(limit: int = 20, offset: int = 0):
        """
        Get all public lists with pagination.

        Args:
            limit: Maximum number of lists to return
            offset: Offset for pagination

        Returns:
            Dictionary with total count and list of List instances
        """
        from src.models.list import List
        from django.db.models import Count

        # Get total count of public lists
        total = List.objects.filter(isPrivate=False).count()
        
        # Get public lists with like count annotation
        lists_qs = (
            List.objects
            .filter(isPrivate=False)
            .annotate(like_count=Count('likes'))
            .order_by('-created_at')[offset:offset + limit]
        )
        
        return {
            'total': total,
            'lists': list(lists_qs)
        }
    
    @staticmethod
    def search_public_lists(query: str, limit: int = 20, offset: int = 0):
        """
        Search public lists by name and description.

        Args:
            query: Search query string
            limit: Maximum number of lists to return
            offset: Offset for pagination

        Returns:
            Dictionary with total count and list of matching List instances
        """
        from src.models.list import List
        from django.db.models import Count, Q

        # Search in list_name or description (case-insensitive)
        filter_query = Q(isPrivate=False)
        if query:
            filter_query &= (Q(list_name__icontains=query) | Q(description__icontains=query))
        
        # Get total count
        total = List.objects.filter(filter_query).count()
        
        # Get lists with like count annotation
        lists_qs = (
            List.objects
            .filter(filter_query)
            .annotate(like_count=Count('likes'))
            .order_by('-created_at')[offset:offset + limit]
        )
        
        return {
            'total': total,
            'lists': list(lists_qs),
            'query': query
        }