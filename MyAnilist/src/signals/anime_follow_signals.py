from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from src.models.anime_follow import AnimeFollow
from src.models.anime_notification import AnimeAiringNotification

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=AnimeFollow)
def cancel_notifications_on_unfollow(sender, instance, **kwargs):
    """
    Cancel all pending notifications when user unfollows an anime.
    """
    cancelled = AnimeAiringNotification.objects.filter(
        user=instance.user,
        anilist_id=instance.anilist_id,
        status='pending'
    ).update(
        status='cancelled',
        updated_at=timezone.now(),
        error_message='User unfollowed anime'
    )
    
    if cancelled > 0:
        logger.info(f"Auto-cancelled {cancelled} notifications for user {instance.user.username} - unfollowed anime {instance.anilist_id}")


@receiver(pre_save, sender=AnimeFollow)
def store_old_anime_follow_state(sender, instance, **kwargs):
    """
    Store old state before save to detect changes.
    """
    if instance.pk:
        try:
            old_instance = AnimeFollow.objects.get(pk=instance.pk)
            instance._old_watch_status = old_instance.watch_status
            instance._old_notify_email = old_instance.notify_email
        except AnimeFollow.DoesNotExist:
            instance._old_watch_status = None
            instance._old_notify_email = None
    else:
        instance._old_watch_status = None
        instance._old_notify_email = None


@receiver(post_save, sender=AnimeFollow)
def handle_anime_follow_changes(sender, instance, created, **kwargs):
    """
    Handle notification status when AnimeFollow is created or updated.
    
    Important: Follow and watch_status are separate concepts:
    - User still "follows" anime even if status is dropped/completed/on_hold
    - Only DELETE (unfollow) should cancel notifications
    - watch_status only affects SCHEDULING (not cancellation)
    
    Actions:
    1. If notify_email cleared → Cancel pending notifications
    2. If notify_email set and watch_status='watching' → Log (will be scheduled)
    3. watch_status changes → No cancellation, just affects future scheduling
    """
    if created:
        # New follow created
        if instance.watch_status == 'watching' and instance.notify_email:
            logger.info(f"User {instance.user.username} started watching anime {instance.anilist_id} - notifications will be scheduled")
        return
    
    # Check for changes
    old_email = getattr(instance, '_old_notify_email', None)
    old_status = getattr(instance, '_old_watch_status', None)
    
    # Only cancel if user explicitly disables email notifications
    if old_email and not instance.notify_email:
        cancelled = AnimeAiringNotification.objects.filter(
            user=instance.user,
            anilist_id=instance.anilist_id,
            status='pending'
        ).update(
            status='cancelled',
            updated_at=timezone.now(),
            error_message='User disabled email notifications'
        )
        
        if cancelled > 0:
            logger.info(f"Auto-cancelled {cancelled} notifications for user {instance.user.username} - anime {instance.anilist_id}: Email disabled")
    
    # Log status changes for monitoring (but don't cancel)
    elif old_status and old_status != instance.watch_status:
        if instance.watch_status == 'watching':
            logger.info(f"User {instance.user.username} resumed watching anime {instance.anilist_id} - new notifications will be scheduled")
        else:
            logger.info(f"User {instance.user.username} changed status for anime {instance.anilist_id}: {old_status} → {instance.watch_status} (notifications kept, scheduling paused)")
