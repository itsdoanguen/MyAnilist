from typing import List, Optional
from ..repositories.staff_repository import StaffRepository
import logging

logger = logging.getLogger(__name__)


class StaffService:
    """Service layer for staff-specific operations."""

    def __init__(self):
        self.repo = StaffRepository()

    def parse_staff(self, staff: dict) -> dict:
        """
        Parse raw staff data from AniList API into a structured format.

        Args:
            staff: Raw staff data from AniList

        Returns:
            Formatted staff dictionary
        """
        name = staff.get('name') or {}
        image = staff.get('image') or {}
        date_of_birth = staff.get('dateOfBirth') or {}
        date_of_death = staff.get('dateOfDeath') or {}
        
        # Format dates
        def format_date(date_dict):
            if not date_dict:
                return None
            year = date_dict.get('year')
            month = date_dict.get('month')
            day = date_dict.get('day')
            if year and month and day:
                return f"{month}/{day}/{year}"
            elif year:
                return str(year)
            return None
        
        # Parse related media (anime/manga appearances) - using staffMedia field
        media_nodes = (staff.get('staffMedia') or {}).get('nodes') or []
        media_list = []
        
        for media in media_nodes:
            title = media.get('title') or {}
            cover_image = media.get('coverImage') or {}
            
            media_list.append({
                'id': media.get('id'),
                'title_romaji': title.get('romaji'),
                'title_english': title.get('english'),
                'cover_image': cover_image.get('large'),
                'type': media.get('type'),
                'format': media.get('format'),
                'status': media.get('status'),
                'episodes': media.get('episodes'),
                'season': media.get('season'),
                'season_year': media.get('seasonYear'),
            })
        
        # Filter only anime (if needed, you can make this configurable)
        anime_appearances = [m for m in media_list if m.get('type') == 'ANIME']
        
        return {
            'id': staff.get('id'),
            'name_full': name.get('full'),
            'name_native': name.get('native'),
            'image': image.get('large'),
            'description': staff.get('description'),
            'language': staff.get('languageV2'),
            'gender': staff.get('gender'),
            'date_of_birth': format_date(date_of_birth),
            'date_of_death': format_date(date_of_death),
            'age': staff.get('age'),
            'years_active': staff.get('yearsActive'),
            'home_town': staff.get('homeTown'),
            'blood_type': staff.get('bloodType'),
            'primary_occupations': staff.get('primaryOccupations') or [],
            'media': media_list,
            'anime_appearances': anime_appearances[:10],  # Limit to 10 most relevant
        }

    def get_staff_by_id(self, staff_id: int) -> dict:
        """
        Get staff details by ID.

        Args:
            staff_id: AniList staff ID

        Returns:
            Formatted staff data
            
        Raises:
            LookupError: If staff not found
        """
        staff = self.repo.fetch_staff_by_id(staff_id)

        if not staff:
            raise LookupError('Staff not found')

        return self.parse_staff(staff)
