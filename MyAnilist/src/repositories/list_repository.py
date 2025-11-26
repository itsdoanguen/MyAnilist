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