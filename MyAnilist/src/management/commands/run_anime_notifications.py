from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from src.services.anime_notification_service import AnimeNotificationService
from src.models.anime_follow import AnimeFollow

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run all anime notification tasks: schedule, send, and cleanup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-schedule',
            action='store_true',
            help='Skip scheduling new notifications'
        )
        parser.add_argument(
            '--skip-send',
            action='store_true',
            help='Skip sending pending notifications'
        )
        parser.add_argument(
            '--skip-cleanup',
            action='store_true',
            help='Skip cleanup of old notifications'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of anime to process for scheduling'
        )
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=30,
            help='Delete notifications older than this many days'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS(f'Starting Anime Notification Tasks at {timezone.now()}'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        notification_service = AnimeNotificationService()
        
        # Task 1: Schedule new notifications
        if not options['skip_schedule']:
            self.stdout.write('\n' + self.style.NOTICE('TASK 1: Scheduling Notifications'))
            self.stdout.write('-'*60)
            self._schedule_notifications(notification_service, options['limit'])
        else:
            self.stdout.write(self.style.WARNING('\nSkipping scheduling task'))
        
        # Task 2: Send pending notifications
        if not options['skip_send']:
            self.stdout.write('\n' + self.style.NOTICE('TASK 2: Sending Pending Notifications'))
            self.stdout.write('-'*60)
            self._send_notifications(notification_service)
        else:
            self.stdout.write(self.style.WARNING('\nSkipping send task'))
        
        # Task 3: Cleanup old notifications
        if not options['skip_cleanup']:
            self.stdout.write('\n' + self.style.NOTICE('TASK 3: Cleaning Up Old Notifications'))
            self.stdout.write('-'*60)
            self._cleanup_notifications(notification_service, options['cleanup_days'])
        else:
            self.stdout.write(self.style.WARNING('\nSkipping cleanup task'))
        
        self.stdout.write('\n' + self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS(f'All tasks completed at {timezone.now()}'))
        self.stdout.write(self.style.SUCCESS('='*60))

    def _schedule_notifications(self, service, limit):
        """Schedule notifications for upcoming episodes"""
        try:
            # Get all unique anime that are being followed
            followed_anime_ids = AnimeFollow.objects.filter(
                notify_email__isnull=False
            ).exclude(
                notify_email=''
            ).values_list('anilist_id', flat=True).distinct()[:limit]
            
            total_anime = len(followed_anime_ids)
            processed = 0
            total_scheduled = 0
            
            self.stdout.write(f'Found {total_anime} followed anime to check')
            
            for anilist_id in followed_anime_ids:
                try:
                    result = service.schedule_notifications_for_anime(anilist_id)
                    
                    if result['success']:
                        scheduled_count = result.get('scheduled', 0)
                        if scheduled_count > 0:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Anime {anilist_id}: Scheduled {scheduled_count} notifications for episode {result.get("episode")}'
                                )
                            )
                            total_scheduled += scheduled_count
                    
                    processed += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error processing anime {anilist_id}: {e}')
                    )
                    logger.exception(f'Error scheduling for anime {anilist_id}: {e}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Schedule complete: {processed}/{total_anime} anime processed, {total_scheduled} notifications scheduled'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Schedule task failed: {e}'))
            logger.exception(f'Schedule task error: {e}')

    def _send_notifications(self, service):
        """Send all pending notifications that are due"""
        try:
            result = service.send_pending_notifications()
            
            sent = result.get('sent', 0)
            failed = result.get('failed', 0)
            
            if sent > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successfully sent {sent} notifications')
                )
            
            if failed > 0:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send {failed} notifications')
                )
            
            if sent == 0 and failed == 0:
                self.stdout.write('No pending notifications to send')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Send task failed: {e}'))
            logger.exception(f'Send task error: {e}')

    def _cleanup_notifications(self, service, days):
        """Delete old notifications"""
        try:
            result = service.cleanup_old_notifications(days)
            deleted = result.get('deleted', 0)
            
            if deleted > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Deleted {deleted} old notifications (older than {days} days)')
                )
            else:
                self.stdout.write(f'No old notifications to delete')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Cleanup task failed: {e}'))
            logger.exception(f'Cleanup task error: {e}')
