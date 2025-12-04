from typing import Optional, List
from django.utils import timezone
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class AnimeNotificationRepository:
    """Repository for anime notification operations"""

    @staticmethod
    def get_user_preference(user):
        """
        Get user's notification preference.

        Args:
            user: User instance

        Returns:
            AnimeNotificationPreference instance or None
        """
        from src.models.anime_notification import AnimeNotificationPreference
        
        try:
            return AnimeNotificationPreference.objects.get(user=user)
        except AnimeNotificationPreference.DoesNotExist:
            return None

    @staticmethod
    def create_or_update_preference(user, **kwargs):
        """
        Create or update user's notification preference.

        Args:
            user: User instance
            **kwargs: Preference fields

        Returns:
            AnimeNotificationPreference instance
        """
        from src.models.anime_notification import AnimeNotificationPreference
        
        preference, created = AnimeNotificationPreference.objects.update_or_create(
            user=user,
            defaults=kwargs
        )
        return preference

    @staticmethod
    def create_notification(user, anilist_id: int, episode_number: int, airing_at, notify_at):
        """
        Create a scheduled notification.

        Args:
            user: User instance
            anilist_id: AniList anime ID
            episode_number: Episode number
            airing_at: DateTime when episode airs
            notify_at: DateTime when to send notification

        Returns:
            AnimeAiringNotification instance or None if already exists
        """
        from src.models.anime_notification import AnimeAiringNotification
        
        try:
            notification, created = AnimeAiringNotification.objects.get_or_create(
                user=user,
                anilist_id=anilist_id,
                episode_number=episode_number,
                defaults={
                    'airing_at': airing_at,
                    'notify_at': notify_at,
                    'status': 'pending'
                }
            )
            return notification if created else None
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None

    @staticmethod
    def get_pending_notifications(limit: int = 100):
        """
        Get pending notifications that are ready to be sent.
        
        Only returns notifications for anime that user is still following with:
        - notify_email set (not empty)
        - watch_status = 'watching'
        
        Also automatically cancels notifications for anime that are no longer followed.

        Args:
            limit: Maximum number of notifications to return

        Returns:
            QuerySet of AnimeAiringNotification
        """
        from src.models.anime_notification import AnimeAiringNotification
        from src.models.anime_follow import AnimeFollow
        from django.db.models import Q, Exists, OuterRef
        
        now = timezone.now()
        
        # Subquery to check if user still follows this anime with correct status
        still_following = AnimeFollow.objects.filter(
            user_id=OuterRef('user_id'),
            anilist_id=OuterRef('anilist_id'),
            watch_status='watching'
        ).exclude(
            notify_email=''
        )
        
        # Get all pending notifications that should be sent
        pending_notifications = AnimeAiringNotification.objects.filter(
            status='pending',
            notify_at__lte=now
        ).annotate(
            is_still_following=Exists(still_following)
        )
        
        # Auto-cancel notifications for anime no longer being watched
        invalid_notifications = pending_notifications.filter(is_still_following=False)
        cancelled_count = invalid_notifications.update(
            status='cancelled',
            updated_at=now,
            error_message='User no longer following or watch_status changed'
        )
        
        if cancelled_count > 0:
            logger.info(f"Auto-cancelled {cancelled_count} notifications for unfollowed/completed anime")
        
        # Return only valid notifications
        return pending_notifications.filter(
            is_still_following=True
        ).select_related('user')[:limit]

    @staticmethod
    def update_notification_status(notification_id: int, status: str, error_message: str = None):
        """
        Update notification status.

        Args:
            notification_id: Notification ID
            status: New status ('sent', 'failed', 'cancelled')
            error_message: Optional error message

        Returns:
            Updated AnimeAiringNotification instance or None
        """
        from src.models.anime_notification import AnimeAiringNotification
        
        try:
            notification = AnimeAiringNotification.objects.get(notification_id=notification_id)
            notification.status = status
            if status == 'sent':
                notification.sent_at = timezone.now()
            if error_message:
                notification.error_message = error_message
            notification.save()
            return notification
        except AnimeAiringNotification.DoesNotExist:
            return None

    @staticmethod
    def get_user_notifications(user, status: str = None, limit: int = 50):
        """
        Get user's notifications.

        Args:
            user: User instance
            status: Optional status filter
            limit: Maximum number to return

        Returns:
            QuerySet of AnimeAiringNotification
        """
        from src.models.anime_notification import AnimeAiringNotification
        
        query = AnimeAiringNotification.objects.filter(user=user)
        if status:
            query = query.filter(status=status)
        return query.order_by('-notify_at')[:limit]

    @staticmethod
    def delete_old_notifications(days: int = 30):
        """
        Delete old notifications that are no longer needed.
        
        Deletes notifications where:
        1. Status is 'cancelled' - Delete immediately (no airing_at check)
        2. Status is 'sent' AND airing_at is older than 'days' parameter
        
        Does NOT delete 'pending' or 'failed' notifications.

        Args:
            days: Keep 'sent' notifications for episodes aired within this many days (default 30)
                  Set to 0 to delete immediately after episode airs
                  Does NOT affect 'cancelled' (always deleted)

        Returns:
            Number of deleted notifications
        """
        from src.models.anime_notification import AnimeAiringNotification
        from django.db.models import Q
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Delete cancelled notifications (regardless of airing_at)
        # AND sent notifications for aired episodes
        deleted_count = AnimeAiringNotification.objects.filter(
            Q(status='cancelled') | 
            Q(status='sent', airing_at__lt=cutoff_date)
        ).delete()[0]
        
        return deleted_count

    @staticmethod
    def get_active_followers_with_preferences():
        """
        Get all users following anime with notification enabled.
        
        Returns users who have:
        1. AnimeFollow with notify_email set (not empty)
        2. watch_status = 'watching' (only currently watching anime)
        3. Either have AnimeNotificationPreference enabled, OR don't have preference (use defaults)

        Returns:
            QuerySet of (user_id, anilist_id, notify_before_hours) tuples
        """
        from src.models.anime_follow import AnimeFollow
        from src.models.anime_notification import AnimeNotificationPreference
        from django.db.models import Q
        
        # Get users who have explicit preferences disabled
        disabled_users = AnimeNotificationPreference.objects.filter(
            Q(enabled=False) | Q(notify_by_email=False)
        ).values_list('user_id', flat=True)
        
        # Get follows with notify_email set, watch_status='watching', excluding disabled users
        # For users without preference, notify_before_hours will be None (will use default 24h)
        return AnimeFollow.objects.filter(
            ~Q(notify_email=''),
            watch_status='watching'
        ).exclude(
            user_id__in=disabled_users
        ).values_list('user_id', 'anilist_id', 'user__anime_notification_preference__notify_before_hours')

    @staticmethod
    def cancel_notifications_for_anime(user, anilist_id: int):
        """
        Cancel all pending notifications for a specific anime.

        Args:
            user: User instance
            anilist_id: AniList anime ID

        Returns:
            Number of cancelled notifications
        """
        from src.models.anime_notification import AnimeAiringNotification
        
        updated = AnimeAiringNotification.objects.filter(
            user=user,
            anilist_id=anilist_id,
            status='pending'
        ).update(status='cancelled', updated_at=timezone.now())
        return updated

    @staticmethod
    def cancel_invalid_notifications():
        """
        Cancel all pending notifications for anime that are no longer being watched.
        
        Checks all pending notifications and cancels those where:
        - User no longer follows the anime
        - User's watch_status is not 'watching' (completed, dropped, on_hold, etc.)
        - User's notify_email is empty

        Returns:
            Number of cancelled notifications
        """
        from src.models.anime_notification import AnimeAiringNotification
        from src.models.anime_follow import AnimeFollow
        from django.db.models import Exists, OuterRef
        
        # Subquery to check if user still follows this anime with correct status
        still_following = AnimeFollow.objects.filter(
            user_id=OuterRef('user_id'),
            anilist_id=OuterRef('anilist_id'),
            watch_status='watching'
        ).exclude(
            notify_email=''
        )
        
        # Find and cancel invalid notifications
        invalid_notifications = AnimeAiringNotification.objects.filter(
            status='pending'
        ).annotate(
            is_still_following=Exists(still_following)
        ).filter(
            is_still_following=False
        )
        
        cancelled_count = invalid_notifications.update(
            status='cancelled',
            updated_at=timezone.now(),
            error_message='User no longer following or watch_status changed'
        )
        
        if cancelled_count > 0:
            logger.info(f"Cancelled {cancelled_count} invalid pending notifications")
        
        return cancelled_count
