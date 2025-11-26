from typing import Optional


class UserListRepository:
    """
    Repository for UserList operations - managing user memberships in lists.
    """

    @staticmethod
    def get_user_list(user, list_id: int):
        """
        Get UserList entry for a user and list.

        Returns UserList instance or None if not found.
        """
        from src.models.list import UserList

        try:
            return UserList.objects.get(user=user, list_id=list_id)
        except UserList.DoesNotExist:
            return None

    @staticmethod
    def add_member_to_list(user, list_obj, is_owner: bool = False, can_edit: bool = False):
        """
        Add a user as a member to a list.

        Args:
            user: User to add
            list_obj: List instance
            is_owner: Whether user is owner (default: False)
            can_edit: Whether user can edit (default: False, means view-only)

        Returns:
            Created UserList instance

        Raises:
            IntegrityError: If user is already a member of the list
        """
        from src.models.list import UserList
        from django.db import IntegrityError

        try:
            user_list = UserList.objects.create(
                user=user,
                list=list_obj,
                is_owner=is_owner,
                can_edit=can_edit
            )
            return user_list
        except IntegrityError:
            raise IntegrityError('User is already a member of this list')

    @staticmethod
    def check_user_is_member(user, list_id: int) -> bool:
        """
        Check if a user is a member of a list.

        Returns:
            True if user is a member, False otherwise
        """
        from src.models.list import UserList

        return UserList.objects.filter(user=user, list_id=list_id).exists()

    @staticmethod
    def get_list_members(list_id: int):
        """
        Get all members of a list.

        Returns:
            List of UserList instances
        """
        from src.models.list import UserList

        return list(UserList.objects.filter(list_id=list_id).select_related('user').order_by('-joined_at'))

    @staticmethod
    def remove_member_from_list(user, list_id: int) -> bool:
        """
        Remove a user from a list.

        Returns:
            True if removed, False if not found
        """
        from src.models.list import UserList

        try:
            user_list = UserList.objects.get(user=user, list_id=list_id)
            user_list.delete()
            return True
        except UserList.DoesNotExist:
            return False

    @staticmethod
    def update_member_permissions(user, list_id: int, can_edit: bool) -> Optional:
        """
        Update member permissions in a list.

        Args:
            user: User to update
            list_id: List ID
            can_edit: New can_edit permission

        Returns:
            Updated UserList instance or None if not found
        """
        from src.models.list import UserList

        try:
            user_list = UserList.objects.get(user=user, list_id=list_id)
            user_list.can_edit = can_edit
            user_list.save()
            return user_list
        except UserList.DoesNotExist:
            return None
