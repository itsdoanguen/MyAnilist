from typing import List, Optional
from ..repositories.anime_repository import AnimeRepository
import logging

logger = logging.getLogger(__name__)


class AnimeService:
    """Service layer for anime-specific operations (detail, characters, etc.)."""

    def __init__(self):
        self.repo = AnimeRepository()

    def _fmt_date(self, d: dict) -> Optional[str]:
        """Format date dictionary to string."""
        if not d:
            return None
        y = d.get('year')
        m = d.get('month')
        day = d.get('day')
        if y and m and day:
            return f"{m}/{day}/{y}"
        return None

    def parse_media(self, media: dict) -> dict:
        """Parse raw media data from AniList API into a structured format."""
        title = media.get('title') or {}
        start = media.get('startDate') or {}
        end = media.get('endDate') or {}
        studios_nodes = (media.get('studios') or {}).get('nodes') if media.get('studios') else None
        studios = [s.get('name') for s in studios_nodes] if studios_nodes else []
        tags_nodes = (media.get('tags') or [])
        tags = [t.get('name') for t in tags_nodes][:10]

        return {
            'id': media.get('id'),
            'name_romaji': title.get('romaji'),
            'name_english': title.get('english'),
            'name_native': title.get('native'),
            'synonyms': media.get('synonyms') or [],
            'starting_time': self._fmt_date(start),
            'ending_time': self._fmt_date(end),
            'cover_image': (media.get('coverImage') or {}).get('large'),
            'banner_image': media.get('bannerImage'),
            'airing_format': media.get('format'),
            'airing_status': media.get('status'),
            'airing_episodes': media.get('episodes'),
            'duration': media.get('duration'),
            'season': media.get('season'),
            'season_year': media.get('seasonYear'),
            'desc': media.get('description'),
            'average_score': media.get('averageScore'),
            'mean_score': media.get('meanScore'),
            'popularity': media.get('popularity'),
            'favourites': media.get('favourites'),
            'trailer': media.get('trailer'),
            'genres': (media.get('genres') or [])[:10],
            'tags': tags,
            'source': media.get('source'),
            'hashtag': media.get('hashtag'),
            'studios': studios,
            'next_airing_ep': media.get('nextAiringEpisode'),
        }

    def get_by_id(self, anime_id: int) -> dict:
        """Get anime details by ID."""
        media = self.repo.fetch_anime_by_id(anime_id)
        if not media:
            raise LookupError('Anime not found')
        return self.parse_media(media)

    def get_overview_data(self, anime_id: int) -> dict:
        """
        Get overview tab data with preview of characters and staff.
        
        Note: Anime details are NOT included - FE should use data from anime_detail endpoint.
        
        Returns:
        - characters: top 6 characters (MAIN roles prioritized)
        - staff: top 3 staff (prioritized by role importance)
        """
        # Fetch characters (fetch more to ensure we get enough MAIN characters)
        try:
            chars_raw = self.repo.fetch_characters_by_anime_id(anime_id, page=1, perpage=20)
            characters = []
            for char in chars_raw:
                node = char.get('node') or {}
                role = char.get('role')
                image = (node.get('image') or {}).get('large')
                
                # Get first voice actor (Japanese preferred)
                vactors_raw = char.get('voiceActors') or []
                voice_actor = None
                for va in vactors_raw:
                    va_node = va or {}
                    va_name = (va_node.get('name') or {})
                    va_lang = (va_node.get('language') or '').strip().upper()
                    if va_lang == 'JAPANESE':
                        voice_actor = {
                            'id': va_node.get('id'),
                            'name_full': va_name.get('full'),
                            'image': (va_node.get('image') or {}).get('large'),
                        }
                        break
                
                characters.append({
                    'id': node.get('id'),
                    'name_full': (node.get('name') or {}).get('full'),
                    'image': image,
                    'role': role,
                    'voice_actor': voice_actor,
                })
            
            # Prioritize MAIN characters first
            mains = [c for c in characters if (c.get('role') or '').upper() == 'MAIN']
            supporting = [c for c in characters if (c.get('role') or '').upper() != 'MAIN']
            
            # Select up to 6: MAIN first, then SUPPORTING
            selected_chars = mains[:6]
            if len(selected_chars) < 6:
                need = 6 - len(selected_chars)
                selected_chars.extend(supporting[:need])
        except Exception:
            logger.exception('Failed to fetch characters preview for anime id %s', anime_id)
            selected_chars = []

        # Fetch staff (top 3)
        try:
            staff_raw = self.repo.fetch_staff_by_anime_id(anime_id, page=1, perpage=20)
            staff_list = []
            for s in staff_raw:
                node = s.get('node') or {}
                role = s.get('role') or ''
                name = node.get('name') or {}
                image = (node.get('image') or {}).get('large')
                
                staff_list.append({
                    'id': node.get('id'),
                    'name_full': name.get('full'),
                    'image': image,
                    'role': role,
                })
            
            # Prioritize important roles (Director, Original Creator, etc.)
            priority_roles = ['Director', 'Original Creator', 'Series Composition', 'Character Design', 'Music']
            
            def get_role_priority(staff_member):
                role = staff_member.get('role') or ''
                for idx, priority_role in enumerate(priority_roles):
                    if priority_role.lower() in role.lower():
                        return idx
                return 999  # Low priority for other roles
            
            staff_list.sort(key=get_role_priority)
            selected_staff = staff_list[:3]
        except Exception:
            logger.exception('Failed to fetch staff preview for anime id %s', anime_id)
            selected_staff = []

        return {
            'characters': selected_chars,
            'staff': selected_staff,
        }

    def get_characters_by_anime_id(self, anime_id: int, language: str = "JAPANESE", page: int = 1, perpage: int = 10) -> List[dict]:
        """
        Fetch characters for a given anime ID.

        Returns a list of characters. Each character includes:
        - id, name_full, image, role, voice_actors: [ {id, name_full, name_native, image, language} ]
        """
        try:
            characters = self.repo.fetch_characters_by_anime_id(anime_id, language=language, page=page, perpage=perpage)
        except Exception:
            logger.exception('Failed to fetch characters for anime id %s', anime_id)
            return []

        if not characters:
            return []

        result = []
        for char in characters:
            node = char.get('node') or {}
            role = char.get('role')
            image = (node.get('image') or {}).get('large')

            vactors_raw = char.get('voiceActors') or []
            voice_actors = []
            lang_filter = (language or '').strip().upper() if language is not None else ''
            for va in vactors_raw:
                va_node = va or {}
                va_name = (va_node.get('name') or {})
                va_image = (va_node.get('image') or {}).get('large')
                va_lang = (va_node.get('language') or '').strip().upper()
                if lang_filter and lang_filter != 'ALL' and va_lang != lang_filter:
                    continue
                voice_actors.append({
                    'id': va_node.get('id'),
                    'name_full': va_name.get('full'),
                    'name_native': va_name.get('native'),
                    'image': va_image,
                    'language': va_node.get('language')
                })

            result.append({
                'id': node.get('id'),
                'name_full': (node.get('name') or {}).get('full'),
                'image': image,
                'role': role,
                'voice_actors': voice_actors,
            })
        return result

    def get_staff_by_anime_id(self, anime_id: int, page: int = 1, perpage: int = 10) -> List[dict]:
        """
        Fetch staff for a given anime ID.

        Returns a list of staff members. Each staff includes:
        - id, name_full, name_native, image, role
        """
        try:
            staff = self.repo.fetch_staff_by_anime_id(anime_id, page=page, perpage=perpage)
        except Exception:
            logger.exception('Failed to fetch staff for anime id %s', anime_id)
            return []

        if not staff:
            return []

        result = []
        for s in staff:
            node = s.get('node') or {}
            role = s.get('role')
            name = node.get('name') or {}
            image = (node.get('image') or {}).get('large')

            result.append({
                'id': node.get('id'),
                'name_full': name.get('full'),
                'name_native': name.get('native'),
                'image': image,
                'role': role,
            })
        return result

    def get_stats_by_anime_id(self, anime_id: int) -> dict:
        """
        Fetch stats and rankings for a given anime ID.

        Returns:
        - average_score: average score out of 100
        - mean_score: mean score out of 100
        - rankings: list of rankings (ranked, popular, etc.)
        - score_distribution: distribution of user scores
        - status_distribution: distribution of user watch statuses
        """
        try:
            stats_data = self.repo.fetch_stats_by_anime_id(anime_id)
        except Exception:
            logger.exception('Failed to fetch stats for anime id %s', anime_id)
            raise

        if not stats_data:
            raise LookupError('Anime stats not found')

        # Parse rankings
        rankings = stats_data.get('rankings') or []
        parsed_rankings = []
        for r in rankings:
            parsed_rankings.append({
                'id': r.get('id'),
                'rank': r.get('rank'),
                'type': r.get('type'),  # RATED or POPULAR
                'format': r.get('format'),
                'year': r.get('year'),
                'season': r.get('season'),
                'all_time': r.get('allTime'),
                'context': r.get('context'),
            })

        # Parse stats
        stats = stats_data.get('stats') or {}
        score_dist = stats.get('scoreDistribution') or []
        status_dist = stats.get('statusDistribution') or []

        return {
            'id': stats_data.get('id'),
            'average_score': stats_data.get('averageScore'),
            'mean_score': stats_data.get('meanScore'),
            'rankings': parsed_rankings,
            'score_distribution': score_dist,
            'status_distribution': status_dist,
        }

    def get_where_to_watch(self, anime_id: int) -> List[dict]:
        """
        Fetch streaming links for a given anime ID.

        Returns a list of streaming services. Each service includes:
        - title, url, site
        """
        try:
            links = self.repo.fetch_where_to_watch(anime_id)
        except Exception:
            logger.exception('Failed to fetch where to watch for anime id %s', anime_id)
            return []

        if not links:
            return []

        result = []
        for link in links:
            result.append({
                'title': link.get('title'),
                'url': link.get('url'),
                'site': link.get('site')
            })
        return result