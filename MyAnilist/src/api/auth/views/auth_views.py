from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import logging

from ..serializers.auth_serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from src.services.user_service import UserService
from src.services.mail_service import MailService
from src.models.email_verification import EmailVerification
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

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
        
        validated_data = serializer.validated_data
        validated_data.pop('confirm_password', None)
        
        user_service = UserService()
        validated_data['email_verified'] = False

        # Wrap creation of user and verification in a transaction so any subsequent
        # error (including mail send failure if we choose to treat it as fatal)
        # will rollback and not leave a partial user row in the database.
        with transaction.atomic():
            user, tokens = user_service.register_user(validated_data)

            verification = EmailVerification.objects.create(
                user=user
            )

            mailer = MailService()
            mail_sent = mailer.send_verification_email(user, verification.token)

            if not mail_sent:
                raise Exception("Failed to send verification email")

        user_data = UserSerializer(user).data

        logger.info(f"User registered successfully: {user.email}")

        resp = {
            'message': 'User registered successfully. Please check your email to verify your account.',
            'user': user_data,
        }

        if not mail_sent:
            resp['warning'] = 'Failed to send verification email. Contact support.'

        return Response(resp, status=status.HTTP_201_CREATED)
        
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
        
        user = serializer.validated_data['user']

        # block login if email not verified
        if not getattr(user, 'email_verified', False):
            return Response({
                'error': 'Email not verified',
                'details': {'non_field_errors': ['Please verify your email before logging in.']}
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update last login time
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
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



@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify email using token passed as query parameter 'token'"""
    token = request.query_params.get('token')
    if not token:
        return Response({
            'error': 'Token missing'
        }, status=status.HTTP_400_BAD_REQUEST)

    verification = EmailVerification.objects.filter(token=token).first()
    if not verification:
        return Response({
            'error': 'Invalid or expired token'
        }, status=status.HTTP_400_BAD_REQUEST)

    if verification.is_expired():
        return Response({
            'error': 'Token expired'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Mark user as verified
    user = verification.user
    user.email_verified = True
    user.save()

    # Optionally, delete or deactivate token
    verification.delete()

    return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)