from typing import Dict, Any, List
from django.utils import timezone
from datetime import timedelta
import logging

from src.repositories.anime_notification_repository import AnimeNotificationRepository
from src.repositories.anime_repository import AnimeRepository
from src.services.mail_service import MailService

logger = logging.getLogger(__name__)


class AnimeNotificationService:
    """Service for managing anime airing notifications"""

    def __init__(self):
        self.notification_repo = AnimeNotificationRepository()
        self.anime_repo = AnimeRepository()
        self.mail_service = MailService()

    def get_user_preference(self, user) -> Dict[str, Any]:
        """
        Get user's notification preferences.

        Args:
            user: User instance

        Returns:
            Dictionary with preference settings
        """
        preference = self.notification_repo.get_user_preference(user)
        if not preference:
            # Return default values
            return {
                'notify_before_hours': 24,
                'enabled': True,
                'notify_by_email': True,
                'notify_in_app': True
            }
        
        return {
            'notify_before_hours': preference.notify_before_hours,
            'enabled': preference.enabled,
            'notify_by_email': preference.notify_by_email,
            'notify_in_app': preference.notify_in_app
        }

    def update_user_preference(self, user, **kwargs) -> Dict[str, Any]:
        """
        Update user's notification preferences.

        Args:
            user: User instance
            **kwargs: Preference fields to update

        Returns:
            Dictionary with updated preference settings
        """
        preference = self.notification_repo.create_or_update_preference(user, **kwargs)
        
        logger.info(f"Updated notification preferences for user {user.username}")
        
        return {
            'notify_before_hours': preference.notify_before_hours,
            'enabled': preference.enabled,
            'notify_by_email': preference.notify_by_email,
            'notify_in_app': preference.notify_in_app
        }

    def schedule_notifications_for_anime(self, anilist_id: int) -> Dict[str, Any]:
        """
        Schedule notifications for an anime's next airing episode.

        Args:
            anilist_id: AniList anime ID

        Returns:
            Dictionary with scheduling results
        """
        try:
            # Fetch anime data from AniList
            anime_data = self.anime_repo.fetch_anime_by_id(anilist_id)
            next_airing = anime_data.get('nextAiringEpisode')
            
            if not next_airing:
                logger.info(f"No upcoming episode for anime {anilist_id}")
                return {
                    'success': False,
                    'message': 'No upcoming episode',
                    'scheduled': 0
                }
            
            airing_at_timestamp = next_airing.get('airingAt')
            episode = next_airing.get('episode')
            
            if not airing_at_timestamp or not episode:
                return {
                    'success': False,
                    'message': 'Invalid airing data',
                    'scheduled': 0
                }
            
            airing_at = timezone.datetime.fromtimestamp(airing_at_timestamp, tz=timezone.get_current_timezone())
            
            # Get all active followers with notification preferences
            followers = self.notification_repo.get_active_followers_with_preferences()
            scheduled_count = 0
            
            for user_id, followed_anilist_id, notify_before_hours in followers:
                if followed_anilist_id != anilist_id:
                    continue
                
                # Use default if preference not set
                hours_before = notify_before_hours if notify_before_hours else 24
                notify_at = airing_at - timedelta(hours=hours_before)
                
                # If notify_at is in the past but episode hasn't aired yet, schedule for immediate sending
                now = timezone.now()
                if notify_at < now < airing_at:
                    # Episode is coming soon but notification time has passed - schedule immediately
                    notify_at = now
                elif notify_at <= now:
                    # Episode has already aired or notification time passed long ago - skip
                    continue
                
                # Create notification
                from src.models import User
                user = User.objects.get(id=user_id)
                notification = self.notification_repo.create_notification(
                    user=user,
                    anilist_id=anilist_id,
                    episode_number=episode,
                    airing_at=airing_at,
                    notify_at=notify_at
                )
                
                if notification:
                    scheduled_count += 1
                    logger.info(f"Scheduled notification for user {user.username} - Anime {anilist_id} Ep {episode}")
            
            return {
                'success': True,
                'message': f'Scheduled {scheduled_count} notifications',
                'scheduled': scheduled_count,
                'episode': episode,
                'airing_at': airing_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling notifications for anime {anilist_id}: {e}")
            return {
                'success': False,
                'message': str(e),
                'scheduled': 0
            }

    def send_pending_notifications(self) -> Dict[str, Any]:
        """
        Send all pending notifications that are due.

        Returns:
            Dictionary with sending results
        """
        pending_notifications = self.notification_repo.get_pending_notifications(limit=100)
        
        sent_count = 0
        failed_count = 0
        
        logger.info(f"Processing {len(pending_notifications)} pending notifications")
        
        for notification in pending_notifications:
            try:
                # Fetch anime info
                anime_data = self.anime_repo.fetch_anime_by_id(notification.anilist_id)
                
                title = anime_data.get('title', {}).get('romaji', f'Anime #{notification.anilist_id}')
                cover_image = anime_data.get('coverImage', {}).get('large', '')
                
                # Calculate time until airing
                time_until = notification.airing_at - timezone.now()
                hours_left = max(0, int(time_until.total_seconds() / 3600))
                
                # Send email
                success = self.mail_service.send_anime_airing_notification(
                    user=notification.user,
                    anime_title=title,
                    episode_number=notification.episode_number,
                    airing_at=notification.airing_at,
                    hours_until_airing=hours_left,
                    cover_image=cover_image,
                    anilist_id=notification.anilist_id
                )
                
                if success:
                    self.notification_repo.update_notification_status(
                        notification.notification_id,
                        'sent'
                    )
                    sent_count += 1
                    logger.info(f"Sent notification {notification.notification_id} to {notification.user.username}")
                else:
                    self.notification_repo.update_notification_status(
                        notification.notification_id,
                        'failed',
                        'Failed to send email'
                    )
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending notification {notification.notification_id}: {e}")
                self.notification_repo.update_notification_status(
                    notification.notification_id,
                    'failed',
                    str(e)
                )
                failed_count += 1
        
        logger.info(f"Notification sending complete: {sent_count} sent, {failed_count} failed")
        
        return {
            'success': True,
            'sent': sent_count,
            'failed': failed_count,
            'total': sent_count + failed_count
        }

    def get_user_notifications(self, user, status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get user's scheduled notifications.

        Args:
            user: User instance
            status: Optional status filter
            limit: Maximum number to return

        Returns:
            List of notification dictionaries
        """
        notifications = self.notification_repo.get_user_notifications(user, status, limit)
        
        result = []
        for notification in notifications:
            result.append({
                'notification_id': notification.notification_id,
                'anilist_id': notification.anilist_id,
                'episode_number': notification.episode_number,
                'airing_at': notification.airing_at.isoformat(),
                'notify_at': notification.notify_at.isoformat(),
                'status': notification.status,
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'error_message': notification.error_message
            })
        
        return result

    def cancel_notifications_for_anime(self, user, anilist_id: int) -> Dict[str, Any]:
        """
        Cancel all pending notifications for a specific anime.

        Args:
            user: User instance
            anilist_id: AniList anime ID

        Returns:
            Dictionary with cancellation results
        """
        cancelled_count = self.notification_repo.cancel_notifications_for_anime(user, anilist_id)
        
        logger.info(f"Cancelled {cancelled_count} notifications for user {user.username} - Anime {anilist_id}")
        
        return {
            'success': True,
            'cancelled': cancelled_count,
            'message': f'Cancelled {cancelled_count} pending notifications'
        }

    def cleanup_old_notifications(self, days: int = 30) -> Dict[str, Any]:
        """
        Delete old notifications and cancel invalid ones.

        Args:
            days: Delete notifications older than this many days

        Returns:
            Dictionary with cleanup results
        """
        # First, cancel invalid pending notifications
        cancelled_count = self.notification_repo.cancel_invalid_notifications()
        
        # Then, delete old notifications
        deleted_count = self.notification_repo.delete_old_notifications(days)
        
        logger.info(f"Cancelled {cancelled_count} invalid notifications, deleted {deleted_count} old notifications")
        
        return {
            'success': True,
            'cancelled': cancelled_count,
            'deleted': deleted_count,
            'message': f'Cancelled {cancelled_count} invalid notifications, deleted {deleted_count} old notifications'
        }
