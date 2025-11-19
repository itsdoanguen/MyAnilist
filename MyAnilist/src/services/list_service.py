from typing import Dict, Any
from django.core.exceptions import ValidationError

from ..repositories.list_repository import ListRepository

logger = __import__('logging').getLogger(__name__)


class ListService:
    """Service for operations around user's custom lists.

    Responsibilities:
    - create/update/delete List records
    - manage UserList associations (permissions, ownership)
    - retrieve lists for users with proper permissions
    """

    def __init__(self):
        self.repo = ListRepository()

    def create_list_for_user(self, user, list_name: str, description: str = '', 
                            is_private: bool = True, color: str = '#3498db') -> Dict[str, Any]:
        """
        Create a new list for a user and automatically set them as owner.

        Args:
            user: User instance creating the list
            list_name: Name of the list
            description: Optional description
            is_private: Whether list is private (default: True)
            color: Hex color code (default: '#3498db')

        Returns:
            Dictionary containing list details

        Raises:
            ValidationError: If validation fails
        """
        # Validate list name
        if not list_name or not list_name.strip():
            raise ValidationError('List name cannot be empty')
        
        if len(list_name) > 255:
            raise ValidationError('List name cannot exceed 255 characters')

        # Validate color format (basic hex validation)
        if color and not (color.startswith('#') and len(color) == 7):
            raise ValidationError('Color must be a valid hex code (e.g., #3498db)')

        try:
            # Create the list
            new_list = self.repo.create_list(
                list_name=list_name.strip(),
                description=description.strip() if description else '',
                is_private=is_private,
                color=color
            )

            # Link user as owner
            user_list = self.repo.create_user_list(
                user=user,
                list_obj=new_list,
                is_owner=True,
                can_edit=True
            )

            return {
                'list_id': new_list.list_id,
                'list_name': new_list.list_name,
                'description': new_list.description,
                'is_private': new_list.isPrivate,
                'color': new_list.color,
                'created_at': new_list.created_at.isoformat() if new_list.created_at else None,
                'updated_at': new_list.updated_at.isoformat() if new_list.updated_at else None,
                'is_owner': user_list.is_owner,
                'can_edit': user_list.can_edit,
            }
        except Exception as e:
            logger.exception('Error creating list for user %s: %s', user.username, e)
            raise

    def get_lists_for_user(self, user):
        """
        Get all lists for a user.

        Returns list of UserList instances.
        """
        return self.repo.get_lists_of_user(user)

    def get_list_details(self, list_id: int):
        """
        Get details of a specific list.

        Returns List instance or None.
        """
        return self.repo.get_details_of_list(list_id)
    
    def get_user_lists(self, target_user, requester_user=None) -> Dict[str, Any]:
        """
        Get all lists for a target user with proper permission filtering.

        Args:
            target_user: User whose lists to retrieve
            requester_user: User making the request (can be None for anonymous)

        Returns:
            Dictionary with user info and their lists

        Logic:
            - If requester is the same as target user: show all lists (private + public)
            - If requester is different or anonymous: show only public lists
        """
        # Check if requester is viewing their own lists
        is_own_lists = requester_user and requester_user.pk == target_user.pk
        
        # Get lists with privacy filter
        list_data = self.repo.get_lists_with_details(
            user=target_user,
            include_private=is_own_lists
        )

        # Format response
        lists = []
        for item in list_data:
            user_list = item['user_list']
            lst = item['list']
            
            lists.append({
                'list_id': lst.list_id,
                'list_name': lst.list_name,
                'description': lst.description,
                'is_private': lst.isPrivate,
                'color': lst.color,
                'created_at': lst.created_at.isoformat() if lst.created_at else None,
                'updated_at': lst.updated_at.isoformat() if lst.updated_at else None,
                'is_owner': user_list.is_owner,
                'can_edit': user_list.can_edit,
                'joined_at': user_list.joined_at.isoformat() if user_list.joined_at else None,
            })

        return {
            'username': target_user.username,
            'total_lists': len(lists),
            'lists': lists,
            'viewing_own': is_own_lists,
        }
    
    def update_list(self, user, list_id: int, list_name: str = None, 
                   description: str = None, color: str = None, 
                   is_private: bool = None) -> Dict[str, Any]:
        """
        Update a list with permission checks.

        Args:
            user: User attempting to update
            list_id: ID of the list to update
            list_name: New name (optional)
            description: New description (optional)
            color: New color (optional)
            is_private: New privacy setting (optional, only owner can change)

        Returns:
            Dictionary containing updated list details

        Raises:
            ValidationError: If validation fails or permission denied
        """
        # Check if list exists
        lst = self.repo.get_details_of_list(list_id)
        if not lst:
            raise ValidationError('List not found')
        
        # Check if user can edit the list
        can_edit = self.repo.check_user_can_edit(user, list_id)
        if not can_edit:
            raise ValidationError('You do not have permission to edit this list')
        
        # Check if user is owner (for privacy changes)
        is_owner = self.repo.check_user_is_owner(user, list_id)
        
        # Validate inputs
        update_fields = {}
        
        if list_name is not None:
            if not list_name.strip():
                raise ValidationError('List name cannot be empty')
            if len(list_name) > 255:
                raise ValidationError('List name cannot exceed 255 characters')
            update_fields['list_name'] = list_name.strip()
        
        if description is not None:
            update_fields['description'] = description.strip()
        
        if color is not None:
            if not (color.startswith('#') and len(color) == 7):
                raise ValidationError('Color must be a valid hex code (e.g., #3498db)')
            update_fields['color'] = color
        
        if is_private is not None:
            # Only owner can change privacy setting
            if not is_owner:
                raise ValidationError('Only the list owner can change privacy settings')
            update_fields['isPrivate'] = is_private
        
        # If no fields to update
        if not update_fields:
            raise ValidationError('No fields to update')
        
        try:
            # Update the list
            updated_list = self.repo.update_list(list_id, **update_fields)
            
            if not updated_list:
                raise ValidationError('Failed to update list')
            
            return {
                'list_id': updated_list.list_id,
                'list_name': updated_list.list_name,
                'description': updated_list.description,
                'is_private': updated_list.isPrivate,
                'color': updated_list.color,
                'created_at': updated_list.created_at.isoformat() if updated_list.created_at else None,
                'updated_at': updated_list.updated_at.isoformat() if updated_list.updated_at else None,
            }
        except Exception as e:
            logger.exception('Error updating list %s: %s', list_id, e)
            raise
