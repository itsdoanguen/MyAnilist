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
            user = User.objects.create_user(
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['password']
            )
            
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
    def get_user_by_username(username: str) -> Optional[Any]:
        """
        Get user by username
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_activity_counts_for_year(user: Any, year: int, include_private: bool = False):
        """
        Query UserActivity counts grouped by date for a given user and year.

        Returns a list of dicts: [{ 'day': date, 'count': int }, ...]
        """
        from src.models import UserActivity
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        qs = UserActivity.objects.filter(user=user, created_at__date__gte=start_date, created_at__date__lte=end_date)
        if not include_private:
            qs = qs.filter(is_public=True)

        qs = (
            qs.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        return list(qs)

    @staticmethod
    def get_activities(user: Any, since_days: int = None, limit: int = 50, offset: int = 0, include_private: bool = False):
        """
        Retrieve UserActivity instances for a user.

        - since_days: if provided, only return activities newer than now - since_days.
        - limit/offset: simple pagination.
        - include_private: whether to include private activities.
        Returns a list of UserActivity model instances ordered by created_at desc.
        """
        from src.models import UserActivity
        from django.utils import timezone
        from datetime import timedelta

        qs = UserActivity.objects.filter(user=user)
        if not include_private:
            qs = qs.filter(is_public=True)

        if since_days is not None:
            cutoff = timezone.now() - timedelta(days=int(since_days))
            qs = qs.filter(created_at__gte=cutoff)

        qs = qs.order_by('-created_at')

        start = int(offset or 0)
        end = start + int(limit or 50)
        return list(qs[start:end])
    
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