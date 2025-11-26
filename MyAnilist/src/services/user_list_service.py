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
