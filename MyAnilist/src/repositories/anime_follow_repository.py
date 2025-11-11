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
