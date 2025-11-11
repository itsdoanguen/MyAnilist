from datetime import date

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from src.services.user_service import UserService


service = UserService()


@api_view(['GET'])
@permission_classes([AllowAny])
def user_activity_heatmap(request, username):
	"""Return daily activity counts for a user for a given year.

	URL: /api/user/{username}/overview/activity?year=YYYY

	- Defaults to the current year if `year` is not provided.
	- If the requester is the same user, private activities are included.
	Response: { "year": 2025, "counts": { "2025-01-01": 0, ... } }
	"""
	# Parse year
	year_q = request.query_params.get('year')
	try:
		year = int(year_q) if year_q else None
	except ValueError:
		return Response({'error': 'year must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	requester = request.user if request.user and request.user.is_authenticated else None

	try:
		payload = service.get_activity_overview(username, year=year, requester=requester)
		return Response(payload, status=status.HTTP_200_OK)
	except ValueError as e:
		if str(e) == 'user_not_found':
			return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
		return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
	except Exception:
		# Log on server side if needed; return generic error to client
		return Response({'error': 'Error fetching activity overview'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_activity_list(request, username):
	"""Return paginated activity items for a user.

	Query params:
	- since_days: integer, optional, limit results to last N days
	- limit: integer, page size (default 50)
	- offset: integer, start offset (default 0)
	"""
	since_q = request.query_params.get('since_days')
	limit_q = request.query_params.get('limit')
	offset_q = request.query_params.get('offset')

	try:
		since_days = int(since_q) if since_q else None
	except ValueError:
		return Response({'error': 'since_days must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		limit = int(limit_q) if limit_q else 50
		offset = int(offset_q) if offset_q else 0
	except ValueError:
		return Response({'error': 'limit and offset must be integers'}, status=status.HTTP_400_BAD_REQUEST)

	requester = request.user if request.user and request.user.is_authenticated else None

	try:
		payload = service.get_activity_list(username, since_days=since_days, limit=limit, offset=offset, requester=requester)
		return Response(payload, status=status.HTTP_200_OK)
	except ValueError as e:
		if str(e) == 'user_not_found':
			return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
		return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
	except Exception:
		return Response({'error': 'Error fetching activity list'}, status=status.HTTP_502_BAD_GATEWAY)

@api_view(['GET'])
@permission_classes([AllowAny])
def user_anime_list(request, username):
	"""Return the anime list for a given user with different statuses.

	Response: {
	  "watching": [ {...}, ... ],
	  "completed": [ {...}, ... ],
	  "on_hold": [ {...}, ... ],
	  "dropped": [ {...}, ... ],
	  "plan_to_watch": [ {...}, ... ]
	}
	"""
	requester = request.user if request.user and request.user.is_authenticated else None

	try:
		payload = service.get_user_anime_list(username, requester=requester)
		return Response(payload, status=status.HTTP_200_OK)
	except ValueError as e:
		if str(e) == 'user_not_found':
			return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
		return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
	except Exception:
		return Response({'error': 'Error fetching user anime list'}, status=status.HTTP_502_BAD_GATEWAY)