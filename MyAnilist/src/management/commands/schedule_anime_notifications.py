from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from src.models.anime_follow import AnimeFollow
from src.services.anime_notification_service import AnimeNotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check followed anime and schedule notifications for upcoming episodes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of anime to process per run'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(self.style.NOTICE(f'Starting notification scheduling (limit: {limit})...'))
        
        notification_service = AnimeNotificationService()
        
        # Get all unique anime that are being followed with email notifications enabled
        # notify_email is a CharField that contains the user's email, so we check it's not empty
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
                self.stdout.write(f'Processing anime {anilist_id}...')
                
                result = notification_service.schedule_notifications_for_anime(anilist_id)
                
                if result['success']:
                    scheduled_count = result.get('scheduled', 0)
                    if scheduled_count > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Scheduled {scheduled_count} notifications for episode {result.get("episode")}'
                            )
                        )
                        total_scheduled += scheduled_count
                    else:
                        self.stdout.write('  - No new notifications scheduled')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ! {result.get("message")}')
                    )
                
                processed += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing anime {anilist_id}: {e}')
                )
                logger.exception(f'Error in schedule_notifications command for anime {anilist_id}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Completed! Processed {processed}/{total_anime} anime, scheduled {total_scheduled} notifications'
            )
        )
