from typing import List, Dict, Any, Optional
import time

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
        start_time = time.time()
        logger.info(f"[PERFORMANCE] Starting get_user_anime_list_for_user for user: {user.username}")
        
        db_start = time.time()
        follows = self.list_follows_for_user(user)
        db_duration = time.time() - db_start
        logger.info(f"[PERFORMANCE] DB query took {db_duration:.3f}s, fetched {len(follows)} follows")

        buckets = {
            'watching': [],
            'completed': [],
            'on_hold': [],
            'dropped': [],
            'plan_to_watch': [],
        }

        api_start = time.time()
        anime_ids = [f.anilist_id for f in follows]
        
        anime_data_map = {}
        batch_count = 0
        for i in range(0, len(anime_ids), 50):
            batch = anime_ids[i:i+50]
            try:
                batch_result = self.anime_repo.fetch_anime_batch(batch)
                anime_data_map.update(batch_result)
                batch_count += 1
            except Exception as e:
                logger.exception(f'Error fetching anime batch {i//50 + 1}: {e}')
        
        api_duration = time.time() - api_start
        logger.info(f"[PERFORMANCE] API batch fetch: {batch_count} batches, {len(anime_data_map)}/{len(anime_ids)} anime fetched in {api_duration:.3f}s")

        processing_start = time.time()
        for f in follows:
            item = {
                'id': f.id,
                'anilist_id': f.anilist_id,
                'episode_progress': f.episode_progress,
                'watch_status': f.watch_status,
                'isFavorite': f.isFavorite,
            }

            anime_data = anime_data_map.get(f.anilist_id)
            if anime_data:
                title = anime_data.get('title') or {}
                cover = (anime_data.get('coverImage') or {}).get('large')
                item.update({
                    'title_romaji': title.get('romaji'),
                    'cover_image': cover,
                    'episodes': anime_data.get('episodes'),
                })

            bucket = f.watch_status if f.watch_status in buckets else 'plan_to_watch'
            buckets[bucket].append(item)

        processing_duration = time.time() - processing_start
        total_duration = time.time() - start_time
        
        logger.info(f"[PERFORMANCE] ===== SUMMARY FOR {user.username} =====")
        logger.info(f"[PERFORMANCE] Total time: {total_duration:.3f}s")
        logger.info(f"[PERFORMANCE] DB query: {db_duration:.3f}s ({db_duration/total_duration*100:.1f}%)")
        logger.info(f"[PERFORMANCE] API batch: {api_duration:.3f}s ({api_duration/total_duration*100:.1f}%)")
        logger.info(f"[PERFORMANCE] Processing: {processing_duration:.3f}s ({processing_duration/total_duration*100:.1f}%)")
        logger.info(f"[PERFORMANCE] Batches: {batch_count}, Success rate: {len(anime_data_map)}/{len(anime_ids)} ({len(anime_data_map)/len(anime_ids)*100:.1f}%)")
        logger.info(f"[PERFORMANCE] =====================================")

        return {
            'username': user.username,
            'counts': {k: len(v) for k, v in buckets.items()},
            **buckets,
        }
