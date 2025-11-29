from typing import List, Dict
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..repositories.anime_list_repository import AnimeListRepository
from ..repositories.list_repository import ListRepository
from ..repositories.user_list_repository import UserListRepository


class AnimeListService:
    """
    Service layer for anime list operations.
    Handles business logic for adding, updating, and removing anime from lists.
    """

    def __init__(self):
        self.anime_list_repo = AnimeListRepository()
        self.list_repo = ListRepository()
        self.user_list_repo = UserListRepository()

    def add_anime_to_list(
        self, 
        user, 
        list_id: int, 
        anilist_id: int, 
        note: str = ''
    ) -> Dict:
        """
        Add an anime to a list.

        Args:
            user: User adding the anime
            list_id: ID of the list
            anilist_id: AniList anime ID
            note: Optional note about the anime

        Returns:
            Dictionary with anime list item details

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        list_obj = self.list_repo.get_details_of_list(list_id)
        if not list_obj:
            raise ValidationError('List not found')

        # Check if user has edit permission
        user_list = self.user_list_repo.get_user_list(user, list_id)
        if not user_list:
            # Check if list is public and user can view it
            if list_obj.isPrivate:
                raise ValidationError('You do not have permission to add anime to this private list')
            raise ValidationError('You are not a member of this list')

        if not user_list.can_edit:
            raise ValidationError('You do not have permission to edit this list')

        # Check if anime already exists in list
        if self.anime_list_repo.check_anime_exists_in_list(list_id, anilist_id):
            raise ValidationError('Anime already exists in this list')

        # Add anime to list
        try:
            anime_item = self.anime_list_repo.add_anime_to_list(
                list_obj=list_obj,
                anilist_id=anilist_id,
                added_by_user=user,
                note=note
            )
        except IntegrityError:
            raise ValidationError('Anime already exists in this list')

        return {
            'id': anime_item.id,
            'list_id': anime_item.list_id,
            'anilist_id': anime_item.anilist_id,
            'note': anime_item.note,
            'added_date': anime_item.added_date.isoformat(),
            'added_by': anime_item.added_by.username if anime_item.added_by else None,
            'message': 'Anime added to list successfully'
        }

    def get_anime_list(self, user, list_id: int) -> Dict:
        """
        Get all anime in a list.

        Args:
            user: User requesting the list (can be None for public lists)
            list_id: ID of the list

        Returns:
            Dictionary with list info and anime items

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        list_obj = self.list_repo.get_details_of_list(list_id)
        if not list_obj:
            raise ValidationError('List not found')

        # Check permissions
        if list_obj.isPrivate:
            if not user or not user.is_authenticated:
                raise ValidationError('Authentication required to view private list')
            
            user_list = self.user_list_repo.get_user_list(user, list_id)
            if not user_list:
                raise ValidationError('You do not have permission to view this private list')

        # Get all anime in list
        anime_items = self.anime_list_repo.get_all_anime_in_list(list_id)

        anime_list = []
        for item in anime_items:
            anime_list.append({
                'id': item.id,
                'anilist_id': item.anilist_id,
                'note': item.note,
                'added_date': item.added_date.isoformat(),
                'added_by': item.added_by.username if item.added_by else None
            })

        return {
            'list_id': list_obj.list_id,
            'list_name': list_obj.list_name,
            'is_private': list_obj.isPrivate,
            'anime_count': len(anime_list),
            'anime_items': anime_list
        }

    def update_anime_note(
        self, 
        user, 
        list_id: int, 
        anilist_id: int, 
        note: str
    ) -> Dict:
        """
        Update the note for an anime in a list.

        Args:
            user: User updating the note
            list_id: ID of the list
            anilist_id: AniList anime ID
            note: New note content

        Returns:
            Dictionary with updated anime details

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        list_obj = self.list_repo.get_details_of_list(list_id)
        if not list_obj:
            raise ValidationError('List not found')

        # Check if user has edit permission
        user_list = self.user_list_repo.get_user_list(user, list_id)
        if not user_list:
            raise ValidationError('You are not a member of this list')

        if not user_list.can_edit:
            raise ValidationError('You do not have permission to edit this list')

        # Check if anime exists in list
        anime_item = self.anime_list_repo.get_anime_in_list(list_id, anilist_id)
        if not anime_item:
            raise ValidationError('Anime not found in this list')

        # Update note
        updated_item = self.anime_list_repo.update_anime_note(list_id, anilist_id, note)

        return {
            'id': updated_item.id,
            'list_id': updated_item.list_id,
            'anilist_id': updated_item.anilist_id,
            'note': updated_item.note,
            'added_date': updated_item.added_date.isoformat(),
            'added_by': updated_item.added_by.username if updated_item.added_by else None,
            'message': 'Anime note updated successfully'
        }

    def remove_anime_from_list(
        self, 
        user, 
        list_id: int, 
        anilist_id: int
    ) -> Dict:
        """
        Remove an anime from a list.

        Args:
            user: User removing the anime
            list_id: ID of the list
            anilist_id: AniList anime ID

        Returns:
            Dictionary with success message

        Raises:
            ValidationError: If validation fails
        """
        # Check if list exists
        list_obj = self.list_repo.get_details_of_list(list_id)
        if not list_obj:
            raise ValidationError('List not found')

        # Check if user has edit permission
        user_list = self.user_list_repo.get_user_list(user, list_id)
        if not user_list:
            raise ValidationError('You are not a member of this list')

        if not user_list.can_edit:
            raise ValidationError('You do not have permission to edit this list')

        # Check if anime exists in list
        if not self.anime_list_repo.check_anime_exists_in_list(list_id, anilist_id):
            raise ValidationError('Anime not found in this list')

        # Remove anime
        deleted = self.anime_list_repo.remove_anime_from_list(list_id, anilist_id)
        if not deleted:
            raise ValidationError('Failed to remove anime from list')

        return {
            'list_id': list_id,
            'anilist_id': anilist_id,
            'message': 'Anime removed from list successfully'
        }
