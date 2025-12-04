from django.core.management.base import BaseCommand
import logging

from src.services.anime_notification_service import AnimeNotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete old anime airing notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='Delete notifications for episodes aired more than X days ago (default: 0 = delete immediately after airing)'
        )

    def handle(self, *args, **options):
        days = options['days']
        
        if days == 0:
            self.stdout.write(self.style.NOTICE('Cleaning up: Cancel invalid notifications + Delete aired episodes immediately'))
        else:
            self.stdout.write(self.style.NOTICE(f'Cleaning up: Cancel invalid notifications + Delete episodes aired >{days} days ago'))
        
        notification_service = AnimeNotificationService()
        result = notification_service.cleanup_old_notifications(days=days)
        
        cancelled = result.get('cancelled', 0)
        deleted = result.get('deleted', 0)
        
        if cancelled > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠ Cancelled {cancelled} invalid pending notifications')
            )
        
        if deleted > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Deleted {deleted} old notifications')
            )
        
        if cancelled == 0 and deleted == 0:
            self.stdout.write(self.style.NOTICE('✓ Nothing to clean up'))
