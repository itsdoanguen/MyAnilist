from typing import List, Dict, Any, Optional

from ..repositories.anime_follow_repository import AnimeFollowRepository
from ..repositories.anime_repository import AnimeRepository

logger = __import__('logging').getLogger(__name__)


class AnimeFollowService:
    """Service for operations around user's anime follows.

    Responsibilities:
    - read/write AnimeFollow records
    - produce the user's anime list grouped by watch status with lightweight
      AniList enrichment (title, cover image, episodes)
    """

    def __init__(self):
        self.repo = AnimeFollowRepository()
        self.anime_repo = AnimeRepository()

    def get_follow(self, user, anilist_id: int):
        """Return AnimeFollow instance or None."""
        return self.repo.get_user_follow_anime_info_by_anilist_id(user, anilist_id)

    def list_follows_for_user(self, user) -> List:
        """Return list of AnimeFollow instances for a user."""
        return self.repo.get_follows_for_user(user)

    def create_or_update_follow(self, user, anilist_id: int, **kwargs):
        """Create or update an AnimeFollow record and return it."""
        return self.repo.create_or_update_anime_follow(user, anilist_id, **kwargs)

    def remove_follow(self, user, anilist_id: int) -> bool:
        """Delete a follow if exists. Returns True if deleted, False if none."""
        f = self.get_follow(user, anilist_id)
        if not f:
            return False
        f.delete()
        return True

    def get_user_anime_list_for_user(self, user) -> Dict[str, Any]:
        """Return the anime list grouped by watch_status for a given user.

        Result matches the previous shape returned by UserService.get_user_anime_list.
        """
        follows = self.list_follows_for_user(user)

        buckets = {
            'watching': [],
            'completed': [],
            'on_hold': [],
            'dropped': [],
            'plan_to_watch': [],
        }

        def enrich(anilist_id: int):
            try:
                data = self.anime_repo.fetch_anime_by_id(anilist_id)
                if not data:
                    return {}

                title = data.get('title') or {}
                cover = (data.get('coverImage') or {}).get('large')
                return {
                    'title_romaji': title.get('romaji'),
                    'title_english': title.get('english'),
                    'title_native': title.get('native'),
                    'cover_image': cover,
                    'episodes': data.get('episodes'),
                }
            except Exception:
                logger.exception('Error enriching anime %s', anilist_id)
                return {}

        for f in follows:
            item = {
                'id': f.id,
                'anilist_id': f.anilist_id,
                'episode_progress': f.episode_progress,
                'watch_status': f.watch_status,
                'is_favorite': f.isFavorite,
                'notify_email': f.notify_email,
                'start_date': f.start_date.isoformat() if f.start_date else None,
                'finish_date': f.finish_date.isoformat() if f.finish_date else None,
                'total_rewatch': f.total_rewatch,
                'user_note': f.user_note,
                'created_at': f.created_at.isoformat() if f.created_at else None,
                'updated_at': f.updated_at.isoformat() if f.updated_at else None,
            }

            enrich_data = enrich(f.anilist_id)
            if enrich_data:
                item.update(enrich_data)

            bucket = f.watch_status if f.watch_status in buckets else 'plan_to_watch'
            buckets[bucket].append(item)

        return {
            'username': user.username,
            'counts': {k: len(v) for k, v in buckets.items()},
            **buckets,
        }
