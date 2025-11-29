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
    def update_member_permissions(user, list_id: int, can_edit: bool) -> Optional: # type: ignore
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

    @staticmethod
    def create_join_request(user, list_obj, request_type: str = 'join', message: str = ''):
        """
        Create a join or edit permission request for a list.

        Args:
            user: User making the request
            list_obj: List instance
            request_type: Type of request ('join' or 'edit_permission')
            message: Optional message from user

        Returns:
            Created ListJoinRequest instance

        Raises:
            IntegrityError: If a pending/approved request already exists
        """
        from src.models.list import ListJoinRequest
        from django.db import IntegrityError

        try:
            join_request = ListJoinRequest.objects.create(
                user=user,
                list=list_obj,
                request_type=request_type,
                message=message,
                status='pending'
            )
            return join_request
        except IntegrityError:
            raise IntegrityError(f'A {request_type} request already exists for this list')

    @staticmethod
    def get_pending_request(user, list_id: int, request_type: str = None):
        """
        Get pending request for a user and list.

        Args:
            user: User instance
            list_id: List ID
            request_type: Optional filter by request type ('join' or 'edit_permission')

        Returns:
            ListJoinRequest instance or None
        """
        from src.models.list import ListJoinRequest

        try:
            filters = {
                'user': user,
                'list_id': list_id,
                'status': 'pending'
            }
            if request_type:
                filters['request_type'] = request_type
            
            return ListJoinRequest.objects.filter(**filters).first()
        except ListJoinRequest.DoesNotExist:
            return None

    @staticmethod
    def get_approved_request(user, list_id: int):
        """
        Get approved join request for a user and list.

        Returns:
            ListJoinRequest instance or None
        """
        from src.models.list import ListJoinRequest

        try:
            return ListJoinRequest.objects.get(
                user=user,
                list_id=list_id,
                status='approved'
            )
        except ListJoinRequest.DoesNotExist:
            return None

    @staticmethod
    def check_has_pending_or_approved_request(user, list_id: int, request_type: str = None) -> bool:
        """
        Check if user has pending or approved request for a list.

        Args:
            user: User instance
            list_id: List ID
            request_type: Optional filter by request type ('join' or 'edit_permission')

        Returns:
            True if exists, False otherwise
        """
        from src.models.list import ListJoinRequest

        filters = {
            'user': user,
            'list_id': list_id,
            'status__in': ['pending', 'approved']
        }
        if request_type:
            filters['request_type'] = request_type
        
        return ListJoinRequest.objects.filter(**filters).exists()

    @staticmethod
    def get_list_pending_requests(list_id: int):
        """
        Get all pending join requests for a list.

        Returns:
            List of ListJoinRequest instances
        """
        from src.models.list import ListJoinRequest

        return list(ListJoinRequest.objects.filter(
            list_id=list_id,
            status='pending'
        ).select_related('user').order_by('-requested_at'))

    @staticmethod
    def get_join_request_by_id(request_id: int):
        """
        Get a join request by ID.

        Returns:
            ListJoinRequest instance or None
        """
        from src.models.list import ListJoinRequest

        try:
            return ListJoinRequest.objects.get(request_id=request_id)
        except ListJoinRequest.DoesNotExist:
            return None

    @staticmethod
    def update_request_status(request_id: int, status: str, responded_by):
        """
        Update join request status.

        Args:
            request_id: Request ID
            status: New status ('approved' or 'rejected')
            responded_by: User who responded to the request

        Returns:
            Updated ListJoinRequest instance or None
        """
        from src.models.list import ListJoinRequest
        from django.utils import timezone

        try:
            join_request = ListJoinRequest.objects.get(request_id=request_id)
            join_request.status = status
            join_request.responded_by = responded_by
            join_request.responded_at = timezone.now()
            join_request.save()
            return join_request
        except ListJoinRequest.DoesNotExist:
            return None
