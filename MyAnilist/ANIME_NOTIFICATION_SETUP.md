# Anime Airing Notification System

## Tổng quan

Hệ thống tự động gửi email thông báo cho users khi anime họ đang follow sắp phát sóng tập mới.

## Cấu trúc

### Models (`src/models/anime_notification.py`)

1. **AnimeNotificationPreference** - Cài đặt thông báo của user
   - `notify_before_hours`: Thông báo trước bao nhiêu giờ (default: 24h)
   - `enabled`: Bật/tắt thông báo
   - `notify_by_email`: Nhận thông báo qua email
   - `notify_in_app`: Nhận thông báo trong app

2. **AnimeAiringNotification** - Lịch thông báo đã được schedule
   - `anilist_id`: ID anime trên AniList
   - `episode_number`: Số tập
   - `airing_at`: Thời gian phát sóng
   - `notify_at`: Thời gian gửi thông báo
   - `status`: pending, sent, failed, cancelled

### API Endpoints

#### 1. Quản lý preferences
```
GET/PUT /api/notification/preferences/
```

**Response:**
```json
{
  "notify_before_hours": 24,
  "enabled": true,
  "notify_by_email": true,
  "notify_in_app": true
}
```

**Update (PUT):**
```json
{
  "notify_before_hours": 48,
  "enabled": true,
  "notify_by_email": true
}
```

#### 2. Xem lịch thông báo của mình
```
GET /api/notification/my/?status=pending&limit=50
```

**Response:**
```json
{
  "notifications": [
    {
      "notification_id": 1,
      "anilist_id": 21,
      "episode_number": 1122,
      "airing_at": "2025-12-05T10:00:00Z",
      "notify_at": "2025-12-04T10:00:00Z",
      "status": "pending",
      "sent_at": null,
      "error_message": null
    }
  ],
  "count": 1
}
```

#### 3. Hủy thông báo cho một anime
```
POST /api/notification/cancel/<anilist_id>/
```

**Response:**
```json
{
  "success": true,
  "cancelled": 3,
  "message": "Cancelled 3 pending notifications"
}
```

## Cài đặt

### Chạy migrations

```bash
python manage.py migrate
```

## Workflow

```
1. User follows anime với notify_email=True
                    ↓
2. Cron/Celery chạy schedule_anime_notifications
   - Fetch nextAiringEpisode từ AniList
   - Tính notify_at = airing_at - notify_before_hours
   - Tạo AnimeAiringNotification (status=pending)
                    ↓
3. Cron/Celery chạy send_anime_notifications
   - Lấy notifications với notify_at <= now và status=pending
   - Gửi email qua MailService
   - Update status=sent hoặc failed
                    ↓
4. User nhận email thông báo anime sắp phát sóng!
```

## Email Template

Email gửi đi sẽ có format:
```
Subject: 🎬 One Piece - Episode 1122 airs in 24h!

Body:
Hello username,

The next episode of "One Piece" is airing soon! 🍿

Episode: 1122
Airing Time: December 05, 2025 at 10:00
Time Until Airing: 24 hours

Don't miss it!

View on MyAniList: https://my-animelist-front.vercel.app/anime/21

---
You're receiving this because you're following this anime.
Manage notification settings: https://my-animelist-front.vercel.app/settings/notifications
```

## Troubleshooting

### Notifications không được tạo
- Check user có follow anime với `notify_email=True` không
- Check user có bật notification preferences không
- Check anime có `nextAiringEpisode` không (anime đã kết thúc thì không có)

### Notifications không được gửi
- Check cron job/celery có chạy không
- Check email configuration trong settings.py
- Check logs: `python manage.py send_anime_notifications`

### Duplicate notifications
- Model có `unique_together = ['user', 'anilist_id', 'episode_number']`
- Không thể tạo duplicate cho cùng user + anime + episode

## Performance

- Schedule command: ~50-100 anime mỗi lần chạy
- Send command: Tối đa 100 notifications mỗi lần
- Database indexes đã được tạo cho queries thường dùng
- Cleanup tự động xóa notifications cũ > 30 ngày

```
