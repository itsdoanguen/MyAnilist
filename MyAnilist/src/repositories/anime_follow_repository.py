from typing import List


class AnimeFollowRepository:
    """
    Repository for AnimeFollow DB operations.
    """

    @staticmethod
    def get_follows_for_user(user) -> List:
        """
        Return a list of AnimeFollow model instances for the given user.

        Ordered by updated_at descending (most recent first).
        """
        from src.models.anime_follow import AnimeFollow

        qs = AnimeFollow.objects.filter(user=user).order_by('-updated_at')
        return list(qs)

    @staticmethod
    def get_user_follow_anime_info_by_anilist_id(user, anilist_id: int):
        """
        Return the AnimeFollow instance for the given user and anilist_id.

        Returns None if not found.
        """
        from src.models.anime_follow import AnimeFollow

        try:
            follow = AnimeFollow.objects.get(user=user, anilist_id=anilist_id)
            return follow
        except AnimeFollow.DoesNotExist:
            return None
        
    @staticmethod
    def create_or_update_anime_follow(user, anilist_id: int, **kwargs):
        """
        Create or update an AnimeFollow entry for the given user and anilist_id.

        kwargs can include any fields of the AnimeFollow model to set/update.
        """
        from src.models.anime_follow import AnimeFollow

        follow, created = AnimeFollow.objects.get_or_create(user=user, anilist_id=anilist_id)
        for key, value in kwargs.items():
            setattr(follow, key, value)

        follow.notify_email = user.email

        follow.save()
        return follow
    
    @staticmethod
    def update_follow(user, anilist_id: int, **kwargs):
        """
        Update fields on an existing AnimeFollow. Returns the updated instance or None.
        """
        from src.models.anime_follow import AnimeFollow

        try:
            follow = AnimeFollow.objects.get(user=user, anilist_id=anilist_id)
        except AnimeFollow.DoesNotExist:
            return None

        for key, value in kwargs.items():
            setattr(follow, key, value)
        follow.save()
        return follow

    @staticmethod
    def delete_follow(user, anilist_id: int) -> bool:
        """Delete the follow record. Returns True if deleted, False if not found."""
        from src.models.anime_follow import AnimeFollow

        try:
            follow = AnimeFollow.objects.get(user=user, anilist_id=anilist_id)
            follow.delete()
            return True
        except AnimeFollow.DoesNotExist:
            return False

    @staticmethod
    def get_follow_by_id(follow_id: int):
        """Return AnimeFollow by PK or None."""
        from src.models.anime_follow import AnimeFollow

        try:
            return AnimeFollow.objects.get(pk=follow_id)
        except AnimeFollow.DoesNotExist:
            return None

    @staticmethod
    def get_follows_for_user_paginated(user, page: int = 1, perpage: int = 50) -> List:
        """Return paginated follows for a user."""
        from src.models.anime_follow import AnimeFollow

        page = max(1, int(page or 1))
        perpage = max(1, int(perpage or 50))
        start = (page - 1) * perpage
        qs = AnimeFollow.objects.filter(user=user).order_by('-updated_at')
        return list(qs[start:start + perpage])

    @staticmethod
    def count_follows_for_user(user) -> int:
        """Return total number of follows for a user."""
        from src.models.anime_follow import AnimeFollow

        return AnimeFollow.objects.filter(user=user).count()

    @staticmethod
    def get_follows_for_user_by_anilist_ids(user, anilist_ids: List[int]) -> List:
        """Return follows for a user filtered by a list of AniList IDs."""
        from src.models.anime_follow import AnimeFollow

        if not anilist_ids:
            return []

        qs = AnimeFollow.objects.filter(user=user, anilist_id__in=anilist_ids).order_by('-updated_at')
        return list(qs)
