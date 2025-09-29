from typing import Dict, Any, Tuple
from django.db import IntegrityError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from ..repositories.user_repository import UserRepository
from ..models.user import User


class UserService:
    """
    Service layer for User business logic
    Contains business rules and coordinates between repository and views
    """
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    def register_user(self, user_data: Dict[str, Any]) -> Tuple[User, Dict[str, str]]:
        """
        Register a new user with business logic validation
        
        Args:
            user_data: Dictionary containing user registration data
            
        Returns:
            Tuple of (User instance, tokens dict)
            
        Raises:
            ValidationError: If validation fails
            IntegrityError: If email/username already exists
        """
        # Validate required fields
        self._validate_registration_data(user_data)
        
        # Check if email already exists
        if self.user_repository.email_exists(user_data['email']):
            raise ValidationError("Email already exists")
        
        # Check if username already exists
        if self.user_repository.username_exists(user_data['username']):
            raise ValidationError("Username already exists")
        
        # Validate password strength
        try:
            validate_password(user_data['password'])
        except ValidationError as e:
            raise ValidationError(f"Password validation failed: {', '.join(e.messages)}")
        
        # Create user through repository
        try:
            user = self.user_repository.create_user(user_data)
            
            # Generate JWT tokens
            tokens = self._generate_tokens(user)
            
            return user, tokens
            
        except IntegrityError as e:
            raise ValidationError(f"Registration failed: {str(e)}")
    
    def _validate_registration_data(self, user_data: Dict[str, Any]) -> None:
        """
        Validate registration data business rules
        
        Args:
            user_data: User registration data
            
        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['username', 'email', 'password']
        
        # Check required fields
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValidationError(f"{field} is required")
        
        # Validate email format (basic check)
        email = user_data['email']
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValidationError("Invalid email format")
        
        # Validate username (no spaces, minimum length)
        username = user_data['username']
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if ' ' in username:
            raise ValidationError("Username cannot contain spaces")
        
        # Validate password minimum length
        password = user_data['password']
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
    
    def _generate_tokens(self, user: User) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens for user
        
        Args:
            user: User instance
            
        Returns:
            Dictionary containing access and refresh tokens
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def get_user_by_email(self, email: str):
        """
        Get user by email through repository
        
        Args:
            email: User email
            
        Returns:
            User instance or None
        """
        return self.user_repository.get_user_by_email(email)
    
    def get_user_by_id(self, user_id: int):
        """
        Get user by ID through repository
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None
        """
        return self.user_repository.get_user_by_id(user_id)