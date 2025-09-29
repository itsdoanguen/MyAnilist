from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from typing import Optional, Dict, Any

User = get_user_model()


class UserRepository:
    """
    Repository pattern for User model
    Handles all database operations related to User
    """
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Optional[Any]:
        """
        Create a new user in the database
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            User: Created user instance
            
        Raises:
            IntegrityError: If email already exists
        """
        try:
            # Use Django's create_user method which handles password hashing
            user = User.objects.create_user(
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['password']
            )
            
            # Set additional fields if provided
            if 'email_verified' in user_data:
                user.email_verified = user_data['email_verified']
                user.save()
            
            return user
            
        except IntegrityError as e:
            if 'email' in str(e):
                raise IntegrityError("Email already exists")
            raise e
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Any]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Any]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def email_exists(email: str) -> bool:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            
        Returns:
            bool: True if email exists, False otherwise
        """
        return User.objects.filter(email=email).exists()
    
    @staticmethod
    def username_exists(username: str) -> bool:
        """
        Check if username already exists
        
        Args:
            username: Username to check
            
        Returns:
            bool: True if username exists, False otherwise
        """
        return User.objects.filter(username=username).exists()