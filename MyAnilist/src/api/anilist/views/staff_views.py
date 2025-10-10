from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

from src.services.staff_service import StaffService

logger = logging.getLogger(__name__)
service = StaffService()


@api_view(['GET'])
@permission_classes([AllowAny])
def staff_detail(request, staff_id):
    """
    Get detailed staff information.

    This endpoint returns comprehensive staff data including:
    - Basic info (name, image, description)
    - All media appearances (anime/manga)
    - Filtered anime appearances
    
    Path parameter:
    - staff_id: integer AniList staff ID

    Response: {
        'id': int,
        'name_full': str,
        'name_native': str,
        'image': str (URL),
        'description': str (HTML formatted),
        'media': [ {id, title_romaji, title_english, cover_image, type, format, status, episodes, season, season_year} ],
    }   
    """
    try:
        staff_id_val = int(staff_id)
    except (TypeError, ValueError):
        return Response({'error': 'staff_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        staff_data = service.get_staff_by_id(staff_id_val)
        return Response(staff_data, status=status.HTTP_200_OK)
    except LookupError:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception('Error fetching staff by id: %s', e)
        return Response({'error': 'Error contacting AniList'}, status=status.HTTP_502_BAD_GATEWAY)
