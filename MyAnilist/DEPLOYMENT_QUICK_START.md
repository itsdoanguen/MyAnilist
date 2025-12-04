# Quick Deployment Guide - PythonAnywhere

## 🚀 Setup trên PythonAnywhere (Free Tier)

### 1. Upload code lên server

```bash
# Trên PythonAnywhere Bash console
cd ~
git clone <your-repo-url> MyAnilist
cd MyAnilist
```

### 2. Setup virtual environment & install packages

```bash
mkvirtualenv myenv --python=/usr/bin/python3.10
pip install -r requirements.txt
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Tạo Scheduled Task

- Vào **Tasks** tab trong PythonAnywhere Dashboard
- Add new scheduled task:

```
Frequency: Daily at 12:00 UTC
Command: /home/doannguyen/.virtualenvs/myenv/bin/python /home/doannguyen/MyAnilist/manage.py run_anime_notifications
```

**Lưu ý:** 
- PythonAnywhere Free chỉ cho 1 task
- Command này chạy cả 3 tasks: schedule → send → cleanup
- Chạy 1 lần/ngày lúc 12:00 UTC (19:00 VN time)

### 5. Test command thủ công

```bash
cd ~/MyAnilist
source ~/.virtualenvs/myenv/bin/activate
python manage.py run_anime_notifications --limit=5
```

## 📊 Command Options

```bash
# Run all tasks (default)
python manage.py run_anime_notifications

# Run with custom limits
python manage.py run_anime_notifications --limit=50 --cleanup-days=60

# Run specific tasks only
python manage.py run_anime_notifications --skip-send --skip-cleanup  # Only schedule
python manage.py run_anime_notifications --skip-schedule --skip-cleanup  # Only send
python manage.py run_anime_notifications --skip-schedule --skip-send  # Only cleanup
```

## ✅ Verify Setup

### Check task logs:
```bash
# Via PythonAnywhere Dashboard
Tasks tab → Click on task name → View logs

# Via console
tail -20 /var/log/doannguyen.pythonanywhere.com.server.log
```

### Check notifications in database:
```bash
python manage.py shell
>>> from src.models.anime_notification import AnimeAiringNotification
>>> print(f"Pending: {AnimeAiringNotification.objects.filter(status='pending').count()}")
>>> print(f"Sent: {AnimeAiringNotification.objects.filter(status='sent').count()}")
```

## 🔧 Troubleshooting

### Task không chạy?
1. Check command path: `/home/doannguyen/.virtualenvs/myenv/bin/python`
2. Check file permissions: `chmod +x ~/MyAnilist/manage.py`
3. View error logs: `cat /var/log/doannguyen.pythonanywhere.com.error.log`

### Không có notifications được tạo?
- ✅ User có follow anime với `notify_email` không rỗng
- ✅ Anime có `nextAiringEpisode` (check trên AniList)
- ✅ User không có preference với `enabled=False`

### Email không được gửi?
- ✅ Check EMAIL_* settings trong `settings.py`
- ✅ Check Gmail "App Password" còn hoạt động
- ✅ Check `notify_at` <= current time

## 📈 Upgrade Options

### PythonAnywhere Hacker ($5/month):
- **Unlimited scheduled tasks** → Có thể tách riêng schedule/send/cleanup
- Better for production với nhiều users
- Recommended frequencies:
  - Schedule: Every 6 hours (00:00, 06:00, 12:00, 18:00)
  - Send: Every 15-30 minutes
  - Cleanup: Daily at 02:00

### Individual commands khi có Hacker plan:
```bash
# Task 1: Schedule (every 6 hours)
/home/doannguyen/.virtualenvs/myenv/bin/python /home/doannguyen/MyAnilist/manage.py schedule_anime_notifications

# Task 2: Send (every 15-30 min)
/home/doannguyen/.virtualenvs/myenv/bin/python /home/doannguyen/MyAnilist/manage.py send_anime_notifications

# Task 3: Cleanup (daily)
/home/doannguyen/.virtualenvs/myenv/bin/python /home/doannguyen/MyAnilist/manage.py cleanup_old_notifications
```

## 🎯 Expected Behavior

**Daily at 12:00 UTC:**
1. **Schedule**: Fetch upcoming episodes từ AniList API → Create notifications cho users
2. **Send**: Gửi email cho notifications có `notify_at <= now`
3. **Cleanup**: Xóa notifications cũ hơn 30 ngày

**Default notification timing:**
- User follow anime → Set `notify_email` = email address
- Episode sắp chiếu → Notification được tạo
- **24 giờ trước khi tập phim chiếu** → Email được gửi
- User có thể customize `notify_before_hours` via API

## 📚 API Endpoints

```bash
# Get/Update notification preferences
GET/PUT /api/notification/preferences/
Body: {
  "notify_before_hours": 24,
  "enabled": true,
  "notify_by_email": true
}

# Get my notifications
GET /api/notification/my/?status=pending

# Cancel notifications for anime
POST /api/notification/cancel/<anilist_id>/
```

## 🔗 Resources

- Full docs: `PRODUCTION_DEPLOYMENT.md`
- API docs: `ANIME_NOTIFICATION_SETUP.md`
- PythonAnywhere Help: https://help.pythonanywhere.com/
