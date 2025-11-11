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
        
        if self.user_repository.email_exists(user_data['email']):
            raise ValidationError("Email already exists")
        
        if self.user_repository.username_exists(user_data['username']):
            raise ValidationError("Username already exists")
        
        try:
            validate_password(user_data['password'])
        except ValidationError as e:
            raise ValidationError(f"Password validation failed: {', '.join(e.messages)}")
        
        try:
            user = self.user_repository.create_user(user_data)
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
        
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValidationError(f"{field} is required")
        
        email = user_data['email']
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValidationError("Invalid email format")
        
        username = user_data['username']
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if ' ' in username:
            raise ValidationError("Username cannot contain spaces")
        
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

    def get_user_by_username(self, username: str):
        """
        Get user by username through repository
        """
        return self.user_repository.get_user_by_username(username)

    def get_activity_overview(self, username: str, year: int = None, requester: User = None):
        """
        Build the activity overview payload for the given username and year.

        - If year is None, uses current year.
        - If requester is the same as the target user, includes private activities.
        Returns a dict: { 'year': year, 'counts': { 'YYYY-MM-DD': int, ... } }
        """
        from datetime import date, datetime, timedelta

        # Resolve user
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError('user_not_found')

        if year is None:
            year = date.today().year

        include_private = requester is not None and requester.pk == user.pk

        rows = self.user_repository.get_activity_counts_for_year(user, year, include_private=include_private)

        # Build zero-filled mapping for full year
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        days = {}
        cur = start_date
        while cur <= end_date:
            days[cur.isoformat()] = 0
            cur = cur + timedelta(days=1)

        for row in rows:
            d = row.get('day')
            if isinstance(d, datetime):
                key = d.date().isoformat()
            else:
                key = d.isoformat()
            days[key] = row.get('count', 0)

        return {'year': year, 'counts': days}

    def get_activity_list(self, username: str, since_days: int = None, limit: int = 50, offset: int = 0, requester: User = None):
        """
        Return a paginated list of user activities formatted for the frontend.

        Each item contains: id, action_type, target_type, target_id, metadata, created_at (iso), ago_seconds
        - since_days: optional integer, limit: page size, offset: start index
        - requester: if requester is the same as user, include private activities
        """
        from django.utils import timezone

        user = self.get_user_by_username(username)
        if not user:
            raise ValueError('user_not_found')

        include_private = requester is not None and requester.pk == user.pk

        activities = self.user_repository.get_activities(user, since_days=since_days, limit=limit, offset=offset, include_private=include_private)

        now = timezone.now()
        result = []
        for a in activities:
            try:
                created = a.created_at
                ago_seconds = int((now - created).total_seconds()) if created else None
            except Exception:
                created = None
                ago_seconds = None

            result.append({
                'id': a.id,
                'action_type': a.action_type,
                'target_type': a.target_type,
                'target_id': a.target_id,
                'metadata': a.metadata,
                'is_public': a.is_public,
                'created_at': created.isoformat() if created else None,
                'ago_seconds': ago_seconds,
            })

        return {
            'username': username,
            'count': len(result),
            'offset': int(offset or 0),
            'limit': int(limit or 50),
            'items': result,
        }

    def get_user_anime_list(self, username: str, requester: User = None):
        """
        Return the anime list for a given user grouped by watch_status.

        Response shape:
        {
          "watching": [ {...}, ... ],
          "completed": [ {...}, ... ],
          "on_hold": [ {...}, ... ],
          "dropped": [ {...}, ... ],
          "plan_to_watch": [ {...}, ... ]
        }

        Each item includes fields from the AnimeFollow model plus a small
        AniList enrichment (title, cover image, episodes) when available.
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError('user_not_found')

        from ..repositories.anime_follow_repository import AnimeFollowRepository
        from ..repositories.anime_repository import AnimeRepository

        follow_repo = AnimeFollowRepository()
        anime_repo = AnimeRepository()

        follows = follow_repo.get_follows_for_user(user)

        buckets = {
            'watching': [],
            'completed': [],
            'on_hold': [],
            'dropped': [],
            'plan_to_watch': [],
        }

        def enrich(anilist_id: int):
            try:
                data = anime_repo.fetch_anime_by_id(anilist_id)
                if not data:
                    return {}

                title = data.get('title') or {}
                cover = (data.get('coverImage') or {}).get('large')
                return {
                    'title_romaji': title.get('romaji'),
                    'title_english': title.get('english'),
                    'title_native': title.get('native'),
                    'cover_image': cover,
                    'episodes': data.get('episodes'),
                }
            except Exception:
                return {}

        for f in follows:
            item = {
                'id': f.id,
                'anilist_id': f.anilist_id,
                'episode_progress': f.episode_progress,
                'watch_status': f.watch_status,
                'is_favorite': f.isFavorite,
                'notify_email': f.notify_email,
                'start_date': f.start_date.isoformat() if f.start_date else None,
                'finish_date': f.finish_date.isoformat() if f.finish_date else None,
                'total_rewatch': f.total_rewatch,
                'user_note': f.user_note,
                'created_at': f.created_at.isoformat() if f.created_at else None,
                'updated_at': f.updated_at.isoformat() if f.updated_at else None,
            }

            enrich_data = enrich(f.anilist_id)
            if enrich_data:
                item.update(enrich_data)

            bucket = f.watch_status if f.watch_status in buckets else 'plan_to_watch'
            buckets[bucket].append(item)

        return {
            'username': username,
            'counts': {k: len(v) for k, v in buckets.items()},
            **buckets,
        }