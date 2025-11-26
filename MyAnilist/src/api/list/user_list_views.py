from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError

from src.services.user_list_service import UserListService
from src.services.user_service import UserService
from .serializers import MemberAddSerializer, MemberPermissionUpdateSerializer

user_list_service = UserListService()
user_service = UserService()

logger = __import__('logging').getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def member_add(request, list_id):
    """Add a member to a list.
    
    Path params:
    - list_id: ID of the list
    
    Body params:
    - username (required): Username of the user to add
    - can_edit (optional, default=False): Permission level
        * True: member can edit the list
        * False: member can only view the list
    
    Permission requirements:
    - Only the list OWNER can add members
    
    Example request:
    POST /api/list/member/1/add/
    {
        "username": "john_doe",
        "can_edit": true
    }
    """
    try:
        owner = request.user
        
        try:
            data = request.data
        except Exception as parse_error:
            logger.warning(f'Failed to parse request data: {parse_error}')
            data = {}
        
        data = data or {}
        
        
        # Validate input
        serializer = MemberAddSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        
        # Get member user by username
        username = validated['username']
        member = user_service.get_user_by_username(username)
        if not member:
            return Response(
                {'error': f'User {username} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add member to list
        result = user_list_service.add_member_to_list(
            owner=owner,
            list_id=list_id,
            member=member,
            can_edit=validated.get('can_edit', False)
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except DRFValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in member_add: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def member_list(request, list_id):
    """Get all members of a list.
    
    Path params:
    - list_id: ID of the list
    
    Permission requirements:
    - Members of the list can view all members
    - Non-members can view members only if list is public
    
    Response includes:
    - List info
    - All members with their permissions (owner/edit/view)
    """
    try:
        requester = request.user if request.user.is_authenticated else None
        
        if not requester:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        result = user_list_service.get_list_members(
            requester=requester,
            list_id=list_id
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except DRFValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in member_list: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def member_remove(request, list_id):
    """Remove a member from a list.
    
    Path params:
    - list_id: ID of the list
    
    Query params:
    - username (required): Username of the member to remove
    
    Permission requirements:
    - Only the list OWNER can remove members
    - Cannot remove the owner
    
    Example: DELETE /api/list/member/1/remove/?username=john_doe
    """
    try:
        owner = request.user
        username = request.query_params.get('username')
        
        if not username:
            return Response(
                {'error': 'Username parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get member user by username
        member = user_service.get_user_by_username(username)
        if not member:
            return Response(
                {'error': f'User {username} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remove member
        user_list_service.remove_member_from_list(
            owner=owner,
            list_id=list_id,
            member=member
        )
        
        return Response({
            'message': f'User {username} removed from list successfully',
            'list_id': list_id,
            'removed_username': username
        }, status=status.HTTP_200_OK)
        
    except DRFValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in member_remove: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def member_permission_update(request, list_id):
    """Update member permissions.
    
    Path params:
    - list_id: ID of the list
    
    Body params:
    - username (required): Username of the member to update
    - can_edit (required): New permission level (true for edit, false for view-only)
    
    Permission requirements:
    - Only the list OWNER can update member permissions
    - Cannot change owner's permissions
    
    Example: PUT /api/list/member/1/permission/
    {
        "username": "john_doe",
        "can_edit": false
    }
    """
    try:
        import json
        
        owner = request.user
        
        try:
            data = request.data
        except Exception as parse_error:
            logger.warning(f'Failed to parse request data: {parse_error}')
            try:
                data = json.loads(request.body)
            except Exception as json_error:
                logger.error(f'Failed to parse JSON from body: {json_error}')
                data = {}
        
        data = data or {}
        
        serializer = MemberPermissionUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        
        username = validated.get('username')
        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member = user_service.get_user_by_username(username)
        if not member:
            return Response(
                {'error': f'User {username} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = user_list_service.update_member_permissions(
            owner=owner,
            list_id=list_id,
            member=member,
            can_edit=validated['can_edit']
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except DRFValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Error in member_permission_update: %s', e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
