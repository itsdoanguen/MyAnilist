from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from src.services.anime_notification_service import AnimeNotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send pending anime airing notifications that are due'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
        
        self.stdout.write(self.style.NOTICE('Checking for pending notifications...'))
        
        notification_service = AnimeNotificationService()
        
        if dry_run:
            # Just show pending notifications
            from src.repositories.anime_notification_repository import AnimeNotificationRepository
            repo = AnimeNotificationRepository()
            pending = repo.get_pending_notifications(limit=100)
            
            self.stdout.write(f'Found {len(pending)} pending notifications:')
            for notif in pending:
                self.stdout.write(
                    f'  - User: {notif.user.username}, Anime: {notif.anilist_id}, '
                    f'Episode: {notif.episode_number}, Notify at: {notif.notify_at}'
                )
            
            self.stdout.write(self.style.SUCCESS('\nDry run complete'))
            return
        
        # Actually send notifications
        result = notification_service.send_pending_notifications()
        
        sent = result.get('sent', 0)
        failed = result.get('failed', 0)
        total = result.get('total', 0)
        
        if sent > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Successfully sent {sent} notifications')
            )
        
        if failed > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to send {failed} notifications')
            )
        
        if total == 0:
            self.stdout.write(self.style.NOTICE('No pending notifications to send'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Completed! {sent}/{total} sent successfully')
            )
