from datetime import date

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
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


@api_view(['GET'])
@permission_classes([AllowAny])
def search_users(request):
	"""Search users by username.

	Query params:
	- q: Search query string (required, min 2 characters)
	- limit: Maximum number of results (default 20, max 50)

	Response: {
	  "query": "search_term",
	  "count": 5,
	  "results": [
		{"id": 1, "username": "user1", "email_verified": true},
		...
	  ]
	}
	"""
	query = request.query_params.get('q', '').strip()
	limit_q = request.query_params.get('limit')

	if not query:
		return Response({'error': 'Query parameter "q" is required'}, status=status.HTTP_400_BAD_REQUEST)

	if len(query) < 2:
		return Response({'error': 'Query must be at least 2 characters long'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		limit = int(limit_q) if limit_q else 20
		limit = min(max(1, limit), 50)  # Clamp between 1 and 50
	except ValueError:
		return Response({'error': 'limit must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		results = service.search_users(query, limit=limit)
		return Response({
			'query': query,
			'count': len(results),
			'results': results
		}, status=status.HTTP_200_OK)
	except Exception as e:
		return Response({'error': 'Error searching users'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
	"""Upload user avatar image.
	
	Request:
	- multipart/form-data with key 'avatar' containing image file
	
	Response:
	{
	  "avatar_url": "/media/avatars/2024/12/user123.jpg",
	  "message": "Avatar updated successfully"
	}
	"""
	from rest_framework.parsers import MultiPartParser, FormParser
	from django.core.exceptions import ValidationError as DjangoValidationError
	
	try:
		avatar_file = request.FILES.get('avatar')
		
		if not avatar_file:
			return Response(
				{'error': 'No avatar file provided'}, 
				status=status.HTTP_400_BAD_REQUEST
			)
		
		result = service.update_avatar(request.user, avatar_file)
		return Response(result, status=status.HTTP_200_OK)
		
	except DjangoValidationError as e:
		return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		return Response({'error': 'Failed to upload avatar'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar(request):
	"""Delete user avatar image.
	
	Response:
	{
	  "message": "Avatar deleted successfully"
	}
	"""
	try:
		result = service.delete_avatar(request.user)
		return Response(result, status=status.HTTP_200_OK)
	except Exception as e:
		return Response({'error': 'Failed to delete avatar'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_profile(request, username):
	"""Get user profile with full information.
	
	Response includes:
	- id, username, email (only for owner)
	- email_verified, avatar_url
	- first_name, last_name
	- last_login, date_joined
	- is_staff, is_active
	"""
	try:
		user = service.get_user_by_username(username)
		if not user:
			return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
		
		# Check if viewing own profile for privacy
		is_own = request.user.is_authenticated and request.user.pk == user.pk
		
		response_data = {
			'id': user.id,
			'username': user.username,
			'email_verified': user.email_verified,
			'avatar_url': user.avatar_url,
			'first_name': user.first_name,
			'last_name': user.last_name,
			'date_joined': user.date_joined.isoformat() if user.date_joined else None,
			'is_staff': user.is_staff,
			'is_active': user.is_active,
			'is_own_profile': is_own,
		}
		
		# Include sensitive info only for own profile
		if is_own:
			response_data['email'] = user.email
			response_data['last_login'] = user.last_login.isoformat() if user.last_login else None
		
		return Response(response_data, status=status.HTTP_200_OK)
		
	except Exception as e:
		return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
	"""Update user profile information.
	
	Body params (all optional):
	- first_name: User's first name
	- last_name: User's last name
	- username: New username (must be unique)
	
	Response: Updated user profile
	"""
	try:
		user = request.user
		data = request.data or {}
		
		updated_fields = []
		
		# Update first_name
		if 'first_name' in data:
			first_name = data['first_name'].strip()
			if len(first_name) > 150:
				return Response(
					{'error': 'first_name cannot exceed 150 characters'},
					status=status.HTTP_400_BAD_REQUEST
				)
			user.first_name = first_name
			updated_fields.append('first_name')
		
		# Update last_name
		if 'last_name' in data:
			last_name = data['last_name'].strip()
			if len(last_name) > 150:
				return Response(
					{'error': 'last_name cannot exceed 150 characters'},
					status=status.HTTP_400_BAD_REQUEST
				)
			user.last_name = last_name
			updated_fields.append('last_name')
		
		# Update username
		if 'username' in data:
			new_username = data['username'].strip()
			
			# Validate username
			if len(new_username) < 3:
				return Response(
					{'error': 'Username must be at least 3 characters long'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			if ' ' in new_username:
				return Response(
					{'error': 'Username cannot contain spaces'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# Check if username already exists (excluding current user)
			from src.models.user import User
			if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
				return Response(
					{'error': 'Username already exists'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			user.username = new_username
			updated_fields.append('username')
		
		# Save changes
		if updated_fields:
			user.save(update_fields=updated_fields)
			return Response({
				'message': 'Profile updated successfully',
				'updated_fields': updated_fields,
				'user': {
					'id': user.id,
					'username': user.username,
					'email': user.email,
					'first_name': user.first_name,
					'last_name': user.last_name,
					'avatar_url': user.avatar_url,
				}
			}, status=status.HTTP_200_OK)
		else:
			return Response(
				{'error': 'No fields to update'},
				status=status.HTTP_400_BAD_REQUEST
			)
		
	except Exception as e:
		return Response({'error': 'Failed to update profile'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
	