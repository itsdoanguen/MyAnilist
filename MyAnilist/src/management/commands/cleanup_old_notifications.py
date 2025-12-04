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
            default=30,
            help='Delete notifications older than this many days (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        
        self.stdout.write(self.style.NOTICE(f'Deleting notifications older than {days} days...'))
        
        notification_service = AnimeNotificationService()
        result = notification_service.cleanup_old_notifications(days=days)
        
        deleted = result.get('deleted', 0)
        
        if deleted > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Deleted {deleted} old notifications')
            )
        else:
            self.stdout.write(self.style.NOTICE('No old notifications to delete'))
