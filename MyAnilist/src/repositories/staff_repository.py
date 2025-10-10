import requests
import logging
from typing import Optional

from .anilist_querys import STAFF_INFO_QS

logger = logging.getLogger(__name__)

class StaffRepository:
    """
    Repository for staff-specific operations on AniList GraphQL API.
    Handles fetching staff details and related media.
    """
    ANILIST_ENDPOINT = 'https://graphql.anilist.co'

    def fetch_staff_by_id(self, staff_id: int) -> Optional[dict]:
        """
        Fetch detailed staff information by ID.

        Args:
            staff_id: AniList staff ID

        Returns:
            Dictionary containing staff details or None

        Raises:
            RuntimeError: If API request fails or returns errors
        """
        payload = {'query': STAFF_INFO_QS, 'variables': {'id': staff_id}}

        try:
            resp = requests.post(self.ANILIST_ENDPOINT, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = e.response.text if getattr(e, 'response', None) is not None else str(e)
            logger.debug('AniList fetch_staff_by_id failed: status=%s body=%s',
                        getattr(e.response, 'status_code', None), body)
            raise RuntimeError(body)
        
        data = resp.json()
        if 'errors' in data:
            logger.debug('AniList returned errors: %s', data['errors'])
            raise RuntimeError(data['errors'])

        return data.get('data', {}).get('Staff')
