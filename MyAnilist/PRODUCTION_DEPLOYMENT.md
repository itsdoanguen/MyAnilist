# Production Deployment Guide - PythonAnywhere Scheduled Tasks

## Tổng quan

Hệ thống anime notification sử dụng **Django Management Commands** và **PythonAnywhere Scheduled Tasks** để tự động hóa việc gửi email thông báo.

## Setup trên PythonAnywhere

1. **Upload code lên PythonAnywhere**

2. **Tạo Scheduled Tasks trong PythonAnywhere Dashboard:**

   - Vào **Tasks** tab
   - Add 3 scheduled tasks sau:

   **Task 1: Schedule Notifications (mỗi 6 giờ)**
   ```
   Frequency: Daily at 00:00, 06:00, 12:00, 18:00
   Command: /home/USERNAME/.virtualenvs/myenv/bin/python /home/USERNAME/MyAnilist/manage.py schedule_anime_notifications
   ```

   **Task 2: Send Notifications (mỗi 15 phút)**
   ```
   Frequency: Hourly at minutes: 0, 15, 30, 45
   Command: /home/USERNAME/.virtualenvs/myenv/bin/python /home/USERNAME/MyAnilist/manage.py send_anime_notifications
   ```

   **Task 3: Cleanup (mỗi ngày lúc 2:00 AM)**
   ```
   Frequency: Daily at 02:00
   Command: /home/USERNAME/.virtualenvs/myenv/bin/python /home/USERNAME/MyAnilist/manage.py cleanup_old_notifications
   ```

3. **Test commands thủ công:**
   ```bash
   cd ~/MyAnilist
   source ~/.virtualenvs/myenv/bin/activate
   python manage.py schedule_anime_notifications --limit=10
   python manage.py send_anime_notifications --dry-run
   ```

4. **View task logs:**
   - Vào **Files** tab → `/var/log/`
   - Check file logs để debug nếu có lỗi

## Testing Locally

### Test commands trước khi deploy:

```bash
# Test schedule (dry run)
python manage.py schedule_anime_notifications --limit=5

# Test send (dry run - không gửi email thật)
python manage.py send_anime_notifications --dry-run

# Test cleanup
python manage.py cleanup_old_notifications --days=30
```

### Test full workflow:

1. **Follow một anime:**
```python
python manage.py shell

from src.models import User, AnimeFollow
user = User.objects.get(username='your_username')
AnimeFollow.objects.create(
    user=user,
    anilist_id=21,  # One Piece
    is_following=True,
    notify_email=True
)
```

2. **Set notification preferences:**
```bash
curl -X PUT http://localhost:8000/api/notification/preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notify_before_hours": 24, "enabled": true, "notify_by_email": true}'
```

3. **Run schedule command:**
```bash
python manage.py schedule_anime_notifications
```

4. **Check created notifications:**
```bash
curl http://localhost:8000/api/notification/my/?status=pending \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Monitoring & Logs

### Check task execution:

**PythonAnywhere:**
- Dashboard → **Tasks** tab
- Click vào task name để xem execution history
- Check `/var/log/` cho detailed logs

**Command line logs:**
```bash
# Xem Django logs
tail -f ~/MyAnilist/logs/django.log

# Xem task-specific logs  
grep "schedule_anime_notifications" ~/MyAnilist/logs/django.log
grep "send_anime_notifications" ~/MyAnilist/logs/django.log
```

### Health checks:

```bash
# Check database có notifications không
python manage.py shell
>>> from src.models import AnimeAiringNotification
>>> print(f"Pending: {AnimeAiringNotification.objects.filter(status='pending').count()}")
>>> print(f"Sent: {AnimeAiringNotification.objects.filter(status='sent').count()}")
```

## Troubleshooting

### Task không chạy trên PythonAnywhere:

**Check 1: Command path đúng chưa?**
```bash
# Test command manually
cd ~/MyAnilist
source ~/.virtualenvs/myenv/bin/activate
python manage.py schedule_anime_notifications
```

**Check 2: Permissions:**
```bash
chmod +x ~/MyAnilist/manage.py
```

**Check 3: View error logs:**
```bash
cat /var/log/USERNAME.pythonanywhere.com.error.log
tail -20 ~/MyAnilist/logs/django.log
```

### Notifications không được tạo:

- ✅ Check user có follow anime với `notify_email=True`
- ✅ Check user có preferences `enabled=True`
- ✅ Check anime có `nextAiringEpisode` (anime finished thì không có)

### Notifications không được gửi:

- ✅ Check email settings trong `settings.py`
- ✅ Test email manually: `python manage.py shell` → call `MailService`
- ✅ Check `notify_at` <= current time

### Duplicate notifications:

- Model có `unique_together = ['user', 'anilist_id', 'episode_number']`
- Không thể tạo duplicate

## Best Practices

### 1. Start với frequency thấp:
- Schedule: 1-2 lần/ngày thay vì 4 lần
- Send: Mỗi giờ thay vì mỗi 15 phút
- Tăng dần khi stable

### 2. Monitor performance:
```bash
# Check execution time
grep "Completed!" ~/MyAnilist/logs/django.log | tail -20
```

### 3. Backup database định kỳ:
```bash
# Backup notifications table
python manage.py dumpdata src.AnimeAiringNotification > backup_notifications.json
```

### 4. Alert khi có errors:
- Setup email alerts trong PythonAnywhere
- Monitor error logs daily

## Chi phí ước tính

- **PythonAnywhere Free:** $0
  - 1 scheduled task per day
  - Good for testing

- **PythonAnywhere Hacker ($5/month):**
  - Unlimited scheduled tasks
  - Good for production

- **PythonAnywhere Web Developer ($12/month):**
  - More resources
  - Better for high traffic
