from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import logging

from ..serializers.auth_serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from src.services.user_service import UserService

# Setup logging
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user
    
    POST /api/auth/register/
    {
        "username": "johndoe",
        "email": "john@example.com",
        "password": "strongpassword123",
        "confirm_password": "strongpassword123"
    }
    
    Returns:
    {
        "message": "User registered successfully",
        "user": {
            "user_id": 1,
            "username": "johndoe",
            "email": "john@example.com",
            "email_verified": false,
            "date_join": "2025-09-29T10:30:00Z"
        },
        "tokens": {
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
    }
    """
    try:
        # Validate input data using serializer
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        validated_data = serializer.validated_data
        # Remove confirm_password as it's not needed for user creation
        validated_data.pop('confirm_password', None)
        
        # Use service layer for business logic
        user_service = UserService()
        user, tokens = user_service.register_user(validated_data)
        
        # Use serializer to format response
        user_data = UserSerializer(user).data
        
        logger.info(f"User registered successfully: {user.email}")
        
        return Response({
            'message': 'User registered successfully',
            'user': user_data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        logger.warning(f"Registration validation error: {str(e)}")
        return Response({
            'error': 'Validation failed',
            'details': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except IntegrityError as e:
        logger.warning(f"Registration integrity error: {str(e)}")
        return Response({
            'error': 'Registration failed',
            'details': {'non_field_errors': ['Email or username already exists']}
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': {'non_field_errors': ['Something went wrong. Please try again.']}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    User login endpoint
    
    POST /api/auth/login/
    {
        "email": "john@example.com",
        "password": "strongpassword123"
    }
    
    Returns:
    {
        "message": "Login successful",
        "user": {
            "user_id": 1,
            "username": "johndoe",
            "email": "john@example.com",
            "email_verified": false,
            "date_join": "2025-09-29T10:30:00Z"
        },
        "tokens": {
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
    }
    """
    try:
        # Validate input data
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get authenticated user from serializer
        user = serializer.validated_data['user']
        
        # Generate tokens using service
        user_service = UserService()
        tokens = user_service._generate_tokens(user)
        
        # Format user data
        user_data = UserSerializer(user).data
        
        logger.info(f"User logged in successfully: {user.email}")
        
        return Response({
            'message': 'Login successful',
            'user': user_data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'details': {'non_field_errors': ['Something went wrong. Please try again.']}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)