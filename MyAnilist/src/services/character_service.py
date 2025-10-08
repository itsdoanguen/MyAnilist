from typing import List, Optional
from ..repositories.character_repository import CharacterRepository
import logging

logger = logging.getLogger(__name__)


class CharacterService:
    """Service layer for character-specific operations."""

    def __init__(self):
        self.repo = CharacterRepository()

    def parse_character(self, character: dict) -> dict:
        """
        Parse raw character data from AniList API into a structured format.
        
        Args:
            character: Raw character data from AniList
            
        Returns:
            Formatted character dictionary
        """
        name = character.get('name') or {}
        image = character.get('image') or {}
        
        # Parse related media (anime/manga appearances)
        media_nodes = (character.get('media') or {}).get('nodes') or []
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
            'id': character.get('id'),
            'name_full': name.get('full'),
            'name_native': name.get('native'),
            'image': image.get('large'),
            'description': character.get('description'),
            'media': media_list,
            'anime_appearances': anime_appearances[:10],  # Limit to 10 most relevant
        }

    def get_character_by_id(self, character_id: int) -> dict:
        """
        Get character details by ID.
        
        Args:
            character_id: AniList character ID
            
        Returns:
            Formatted character data
            
        Raises:
            LookupError: If character not found
        """
        character = self.repo.fetch_character_by_id(character_id)
        
        if not character:
            raise LookupError('Character not found')
        
        return self.parse_character(character)
