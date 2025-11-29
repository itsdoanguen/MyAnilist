from typing import Dict, Any
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..repositories.user_list_repository import UserListRepository
from ..repositories.list_repository import ListRepository

logger = __import__('logging').getLogger(__name__)


class UserListService:
    """Service for managing user memberships in lists.

    Responsibilities:
    - add/remove members from lists
    - manage member permissions (view/edit)
    - validate ownership permissions for member management
    """

    def __init__(self):
        self.user_list_repo = UserListRepository()
        self.list_repo = ListRepository()

    def add_member_to_list(self, owner, list_id: int, member, can_edit: bool = False) -> Dict[str, Any]:
        """
        Add a member to a list. Only the owner can add members.

        Args:
            owner: User attempting to add member (must be owner)
            list_id: ID of the list
            member: User to be added as member
            can_edit: Whether member can edit (True) or only view (False, default)

        Returns:
            Dictionary containing member info

        Raises:
            ValidationError: If validation or permission fails
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if requester is owner
        is_owner = self.list_repo.check_user_is_owner(owner, list_id)
        if not is_owner:
            raise ValidationError('Only the list owner can add members')

        # Check if member is the owner themselves
        if owner.pk == member.pk:
            raise ValidationError('You cannot add yourself as a member (you are already the owner)')

        # Check if member is already in the list
        if self.user_list_repo.check_user_is_member(member, list_id):
            raise ValidationError(f'User {member.username} is already a member of this list')

        try:
            # Add member with specified permissions
            user_list = self.user_list_repo.add_member_to_list(
                user=member,
                list_obj=lst,
                is_owner=False,
                can_edit=can_edit
            )

            return {
                'user_id': member.pk,
                'username': member.username,
                'list_id': lst.list_id,
                'list_name': lst.list_name,
                'is_owner': user_list.is_owner,
                'can_edit': user_list.can_edit,
                'joined_at': user_list.joined_at.isoformat() if user_list.joined_at else None,
                'permission_level': 'edit' if can_edit else 'view',
            }
        except IntegrityError as e:
            logger.exception('Error adding member to list %s: %s', list_id, e)
            raise ValidationError('User is already a member of this list')
        except Exception as e:
            logger.exception('Error adding member to list %s: %s', list_id, e)
            raise

    def get_list_members(self, requester, list_id: int) -> Dict[str, Any]:
        """
        Get all members of a list.

        Args:
            requester: User requesting member list
            list_id: ID of the list

        Returns:
            Dictionary with list info and members

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if requester is a member of the list
        if not self.user_list_repo.check_user_is_member(requester, list_id):
            # If not a member, check if list is public
            if lst.isPrivate:
                raise ValidationError('You do not have permission to view members of this private list')

        # Get all members
        members = self.user_list_repo.get_list_members(list_id)

        member_list = []
        for user_list in members:
            member_list.append({
                'user_id': user_list.user.pk,
                'username': user_list.user.username,
                'is_owner': user_list.is_owner,
                'can_edit': user_list.can_edit,
                'joined_at': user_list.joined_at.isoformat() if user_list.joined_at else None,
                'permission_level': 'owner' if user_list.is_owner else ('edit' if user_list.can_edit else 'view'),
            })

        return {
            'list_id': lst.list_id,
            'list_name': lst.list_name,
            'total_members': len(member_list),
            'members': member_list,
        }

    def remove_member_from_list(self, owner, list_id: int, member) -> bool:
        """
        Remove a member from a list. Only owner can remove members.

        Args:
            owner: User attempting to remove member (must be owner)
            list_id: ID of the list
            member: User to remove

        Returns:
            True if removed successfully

        Raises:
            ValidationError: If validation or permission fails
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if requester is owner
        is_owner = self.list_repo.check_user_is_owner(owner, list_id)
        if not is_owner:
            raise ValidationError('Only the list owner can remove members')

        # Check if trying to remove owner themselves
        member_user_list = self.user_list_repo.get_user_list(member, list_id)
        if member_user_list and member_user_list.is_owner:
            raise ValidationError('Cannot remove the owner from the list')

        # Remove member
        removed = self.user_list_repo.remove_member_from_list(member, list_id)
        if not removed:
            raise ValidationError(f'User {member.username} is not a member of this list')

        return True

    def update_member_permissions(self, owner, list_id: int, member, can_edit: bool) -> Dict[str, Any]:
        """
        Update member permissions. Only owner can update permissions.

        Args:
            owner: User attempting to update (must be owner)
            list_id: ID of the list
            member: User whose permissions to update
            can_edit: New can_edit permission

        Returns:
            Dictionary containing updated member info

        Raises:
            ValidationError: If validation or permission fails
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if requester is owner
        is_owner = self.list_repo.check_user_is_owner(owner, list_id)
        if not is_owner:
            raise ValidationError('Only the list owner can update member permissions')

        # Check if trying to update owner's permissions
        member_user_list = self.user_list_repo.get_user_list(member, list_id)
        if not member_user_list:
            raise ValidationError(f'User {member.username} is not a member of this list')

        if member_user_list.is_owner:
            raise ValidationError('Cannot change permissions of the list owner')

        # Update permissions
        updated = self.user_list_repo.update_member_permissions(member, list_id, can_edit)
        if not updated:
            raise ValidationError('Failed to update member permissions')

        return {
            'user_id': member.pk,
            'username': member.username,
            'list_id': lst.list_id,
            'list_name': lst.list_name,
            'is_owner': updated.is_owner,
            'can_edit': updated.can_edit,
            'joined_at': updated.joined_at.isoformat() if updated.joined_at else None,
            'permission_level': 'edit' if can_edit else 'view',
        }

    def create_join_request(self, user, list_id: int, message: str = '') -> Dict[str, Any]:
        """
        Create a join request for a list.

        Validation rules:
        - List must exist and be public
        - User cannot be the owner of the list
        - User cannot already be a member of the list
        - User cannot have pending or approved request for this list

        Args:
            user: User requesting to join
            list_id: ID of the list
            message: Optional message from user

        Returns:
            Dictionary containing join request info

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if list is public
        if lst.isPrivate:
            raise ValidationError('You can only request to join public lists')

        # Check if user is the owner
        is_owner = self.list_repo.check_user_is_owner(user, list_id)
        if is_owner:
            raise ValidationError('You cannot request to join your own list')

        # Check if user is already a member
        if self.user_list_repo.check_user_is_member(user, list_id):
            raise ValidationError('You are already a member of this list')

        # Check if user has pending or approved request
        if self.user_list_repo.check_has_pending_or_approved_request(user, list_id):
            raise ValidationError('You already have a pending or approved request for this list')

        try:
            join_request = self.user_list_repo.create_join_request(
                user=user,
                list_obj=lst,
                message=message
            )

            return {
                'request_id': join_request.request_id,
                'user_id': user.pk,
                'username': user.username,
                'list_id': lst.list_id,
                'list_name': lst.list_name,
                'message': join_request.message,
                'status': join_request.status,
                'requested_at': join_request.requested_at.isoformat() if join_request.requested_at else None,
            }
        except IntegrityError as e:
            logger.exception('Error creating join request for list %s: %s', list_id, e)
            raise ValidationError('A join request already exists for this list')
        except Exception as e:
            logger.exception('Error creating join request for list %s: %s', list_id, e)
            raise

    def get_list_join_requests(self, owner, list_id: int) -> Dict[str, Any]:
        """
        Get all pending join requests for a list. Only owner can view.

        Args:
            owner: User requesting (must be owner)
            list_id: ID of the list

        Returns:
            Dictionary with list info and pending requests

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if requester is owner
        is_owner = self.list_repo.check_user_is_owner(owner, list_id)
        if not is_owner:
            raise ValidationError('Only the list owner can view join requests')

        # Get all pending requests
        requests = self.user_list_repo.get_list_pending_requests(list_id)

        request_list = []
        for req in requests:
            request_list.append({
                'request_id': req.request_id,
                'user_id': req.user.pk,
                'username': req.user.username,
                'message': req.message,
                'status': req.status,
                'requested_at': req.requested_at.isoformat() if req.requested_at else None,
            })

        return {
            'list_id': lst.list_id,
            'list_name': lst.list_name,
            'total_requests': len(request_list),
            'requests': request_list,
        }

    def respond_to_join_request(self, owner, list_id: int, request_id: int, action: str, can_edit: bool = False) -> Dict[str, Any]:
        """
        Respond to a join request (approve or reject). Only owner can respond.

        Args:
            owner: User responding (must be owner)
            list_id: ID of the list
            request_id: ID of the join request
            action: 'approve' or 'reject'
            can_edit: Permission level when approving (ignored for reject)

        Returns:
            Dictionary containing response info

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if requester is owner
        is_owner = self.list_repo.check_user_is_owner(owner, list_id)
        if not is_owner:
            raise ValidationError('Only the list owner can respond to join requests')

        # Get join request
        join_request = self.user_list_repo.get_join_request_by_id(request_id)
        if not join_request:
            raise ValidationError('Join request not found')

        # Verify request belongs to this list
        if join_request.list_id != list_id:
            raise ValidationError('Join request does not belong to this list')

        # Check if request is pending
        if join_request.status != 'pending':
            raise ValidationError(f'Join request has already been {join_request.status}')

        try:
            if action == 'approve':
                # Add user as member
                user_list = self.user_list_repo.add_member_to_list(
                    user=join_request.user,
                    list_obj=lst,
                    is_owner=False,
                    can_edit=can_edit
                )

                updated_request = self.user_list_repo.update_request_status(
                    request_id=request_id,
                    status='approved',
                    responded_by=owner
                )

                return {
                    'action': 'approved',
                    'request_id': request_id,
                    'user_id': join_request.user.pk,
                    'username': join_request.user.username,
                    'list_id': lst.list_id,
                    'list_name': lst.list_name,
                    'can_edit': can_edit,
                    'permission_level': 'edit' if can_edit else 'view',
                    'responded_at': updated_request.responded_at.isoformat() if updated_request and updated_request.responded_at else None,
                }

            else:  # reject
                updated_request = self.user_list_repo.update_request_status(
                    request_id=request_id,
                    status='rejected',
                    responded_by=owner
                )

                return {
                    'action': 'rejected',
                    'request_id': request_id,
                    'user_id': join_request.user.pk,
                    'username': join_request.user.username,
                    'list_id': lst.list_id,
                    'list_name': lst.list_name,
                    'responded_at': updated_request.responded_at.isoformat() if updated_request and updated_request.responded_at else None,
                }

        except IntegrityError as e:
            logger.exception('Error responding to join request %s: %s', request_id, e)
            raise ValidationError('User is already a member of this list')
        except Exception as e:
            logger.exception('Error responding to join request %s: %s', request_id, e)
            raise

    def check_user_list_status(self, user, list_id: int) -> Dict[str, Any]:
        """
        Check user's relationship and available actions with a list.

        Args:
            user: User to check status for
            list_id: ID of the list

        Returns:
            Dictionary containing user's status and permissions:
            - is_owner: Whether user owns the list
            - is_member: Whether user is a member
            - can_edit: Whether user can edit (if member)
            - has_pending_request: Whether user has a pending join request
            - can_request_join: Whether user can request to join
            - is_public: Whether the list is public
            - pending_requests_count: Number of pending requests (if owner)

        Raises:
            ValidationError: If list not found
        """
        # Check if list exists
        lst = self.list_repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')

        # Check if user is a member
        user_list = self.user_list_repo.get_user_list(user, list_id)
        is_owner = user_list.is_owner if user_list else False
        is_member = user_list is not None
        can_edit = user_list.can_edit if user_list else False

        # Check if user has pending request
        pending_request = self.user_list_repo.get_pending_request(user, list_id)
        has_pending_request = pending_request is not None

        # User can request to join if:
        # - List is public
        # - User is not the owner
        # - User is not already a member
        # - User does not have a pending request
        can_request_join = (
            not lst.isPrivate and
            not is_owner and
            not is_member and
            not has_pending_request
        )

        result = {
            'is_owner': is_owner,
            'is_member': is_member,
            'can_edit': can_edit,
            'has_pending_request': has_pending_request,
            'can_request_join': can_request_join,
            'is_public': not lst.isPrivate,
        }

        # If user is owner, add pending requests count
        if is_owner:
            pending_requests = self.user_list_repo.get_list_pending_requests(list_id)
            result['pending_requests_count'] = len(pending_requests)

        return result
