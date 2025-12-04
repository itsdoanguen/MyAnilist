import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyAnilist.settings')
django.setup()

from src.models import User, AnimeFollow
from src.models.anime_notification import AnimeAiringNotification
from django.utils import timezone
from datetime import timedelta

print("=== TEST ANIME FOLLOW SIGNALS ===\n")

# Get or create test user
user, _ = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)

# Test anime ID
test_anime = 21  # One Piece

print("1. Cleanup existing data")
AnimeFollow.objects.filter(user=user, anilist_id=test_anime).delete()
AnimeAiringNotification.objects.filter(user=user, anilist_id=test_anime).delete()

print("\n2. Create anime follow with watching status")
follow = AnimeFollow.objects.create(
    user=user,
    anilist_id=test_anime,
    watch_status='watching',
    notify_email='test@example.com'
)
print(f"   Created follow: {follow.watch_status}, email: {follow.notify_email}")

print("\n3. Create test notification (simulating scheduled notification)")
notification = AnimeAiringNotification.objects.create(
    user=user,
    anilist_id=test_anime,
    episode_number=1000,
    airing_at=timezone.now() + timedelta(days=1),
    notify_at=timezone.now(),
    status='pending'
)
print(f"   Created notification #{notification.notification_id}: status={notification.status}")

print("\n4. TEST: Change watch_status to 'completed'")
follow.watch_status = 'completed'
follow.save()
notification.refresh_from_db()
print(f"   Notification status: {notification.status}")
print(f"   Error message: {notification.error_message}")

print("\n5. Create new notification")
notification2 = AnimeAiringNotification.objects.create(
    user=user,
    anilist_id=test_anime,
    episode_number=1001,
    airing_at=timezone.now() + timedelta(days=2),
    notify_at=timezone.now() + timedelta(hours=1),
    status='pending'
)
print(f"   Created notification #{notification2.notification_id}: status={notification2.status}")

print("\n6. TEST: Change watch_status back to 'watching'")
follow.watch_status = 'watching'
follow.save()
notification2.refresh_from_db()
print(f"   Notification status: {notification2.status}")
print(f"   Should still be 'pending' (will be scheduled new ones by schedule task)")

print("\n7. TEST: Clear notify_email")
follow.notify_email = ''
follow.save()
notification2.refresh_from_db()
print(f"   Notification status: {notification2.status}")
print(f"   Error message: {notification2.error_message}")

print("\n8. Create another notification")
notification3 = AnimeAiringNotification.objects.create(
    user=user,
    anilist_id=test_anime,
    episode_number=1002,
    airing_at=timezone.now() + timedelta(days=3),
    notify_at=timezone.now() + timedelta(hours=2),
    status='pending'
)
print(f"   Created notification #{notification3.notification_id}: status={notification3.status}")

print("\n9. TEST: Unfollow anime (delete follow)")
follow.delete()
notification3.refresh_from_db()
print(f"   Notification status: {notification3.status}")
print(f"   Error message: {notification3.error_message}")

print("\n=== ALL TESTS COMPLETED ===")
print("\nSummary:")
print(f"  Notification #1 (completed): {AnimeAiringNotification.objects.get(pk=notification.pk).status}")
print(f"  Notification #2 (email cleared): {AnimeAiringNotification.objects.get(pk=notification2.pk).status}")
print(f"  Notification #3 (unfollowed): {AnimeAiringNotification.objects.get(pk=notification3.pk).status}")
