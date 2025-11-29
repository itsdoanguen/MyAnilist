from typing import List, Optional
from django.db.models import QuerySet

from src.models.list import AnimeList


class AnimeListRepository:
    """
    Repository for AnimeList DB operations.
    Handles CRUD operations for anime items within lists.
    """

    @staticmethod
    def add_anime_to_list(list_obj, anilist_id: int, added_by_user, note: str = '') -> 'AnimeList': # type: ignore
        """
        Add an anime to a list.

        Args:
            list_obj: List instance
            anilist_id: AniList anime ID
            added_by_user: User who added the anime
            note: Optional note about the anime

        Returns:
            Created AnimeList instance

        Raises:
            IntegrityError: If anime already exists in the list
        """
        from src.models.list import AnimeList

        anime_list_item = AnimeList.objects.create(
            list=list_obj,
            anilist_id=anilist_id,
            added_by=added_by_user,
            note=note
        )
        return anime_list_item

    @staticmethod
    def get_anime_in_list(list_id: int, anilist_id: int) -> Optional['AnimeList']: # type: ignore
        """
        Get a specific anime item in a list.

        Args:
            list_id: List ID
            anilist_id: AniList anime ID

        Returns:
            AnimeList instance or None if not found
        """
        from src.models.list import AnimeList

        try:
            return AnimeList.objects.get(list_id=list_id, anilist_id=anilist_id)
        except AnimeList.DoesNotExist:
            return None

    @staticmethod
    def get_all_anime_in_list(list_id: int) -> QuerySet:
        """
        Get all anime items in a list.

        Args:
            list_id: List ID

        Returns:
            QuerySet of AnimeList instances ordered by added_date descending
        """
        from src.models.list import AnimeList

        return AnimeList.objects.filter(list_id=list_id).order_by('-added_date')

    @staticmethod
    def update_anime_note(list_id: int, anilist_id: int, note: str) -> Optional['AnimeList']:
        """
        Update the note for an anime in a list.

        Args:
            list_id: List ID
            anilist_id: AniList anime ID
            note: New note content

        Returns:
            Updated AnimeList instance or None if not found
        """
        from src.models.list import AnimeList

        try:
            anime_item = AnimeList.objects.get(list_id=list_id, anilist_id=anilist_id)
            anime_item.note = note
            anime_item.save()
            return anime_item
        except AnimeList.DoesNotExist:
            return None

    @staticmethod
    def remove_anime_from_list(list_id: int, anilist_id: int) -> bool:
        """
        Remove an anime from a list.

        Args:
            list_id: List ID
            anilist_id: AniList anime ID

        Returns:
            True if deleted successfully, False if not found
        """
        from src.models.list import AnimeList

        try:
            anime_item = AnimeList.objects.get(list_id=list_id, anilist_id=anilist_id)
            anime_item.delete()
            return True
        except AnimeList.DoesNotExist:
            return False

    @staticmethod
    def check_anime_exists_in_list(list_id: int, anilist_id: int) -> bool:
        """
        Check if an anime exists in a list.

        Args:
            list_id: List ID
            anilist_id: AniList anime ID

        Returns:
            True if anime exists in list, False otherwise
        """
        from src.models.list import AnimeList

        return AnimeList.objects.filter(list_id=list_id, anilist_id=anilist_id).exists()

    @staticmethod
    def get_anime_count_in_list(list_id: int) -> int:
        """
        Get the total count of anime in a list.

        Args:
            list_id: List ID

        Returns:
            Count of anime items in the list
        """
        from src.models.list import AnimeList

        return AnimeList.objects.filter(list_id=list_id).count()
