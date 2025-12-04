# Production Deployment Guide - PythonAnywhere Scheduled Tasks

## Tổng quan

Hệ thống anime notification sử dụng **Django Management Commands** và **PythonAnywhere Scheduled Tasks** để tự động hóa việc gửi email thông báo.

## Setup trên PythonAnywhere

1. **Upload code lên PythonAnywhere**

2. **Tạo Scheduled Task trong PythonAnywhere Dashboard:**

   - Vào **Tasks** tab
   - Add scheduled task:

   **All-in-One Task (chạy mỗi ngày lúc 12:00)**
   ```
   Frequency: Daily at 12:00 UTC
   Command: /home/doannguyen/.virtualenvs/myenv/bin/python /home/doannguyen/MyAnilist/manage.py run_anime_notifications
   ```

   **Lưu ý:** 
   - PythonAnywhere Free chỉ cho phép 1 scheduled task
   - Command này sẽ chạy cả 3 tasks: schedule → send → cleanup
   - Chạy 1 lần/ngày là đủ cho hầu hết use cases
   - Nếu cần chạy nhiều lần hơn, upgrade lên Hacker plan ($5/month)

3. **Test command thủ công:**
   ```bash
   cd ~/MyAnilist
   source ~/.virtualenvs/myenv/bin/activate
   
   # Run all tasks
   python manage.py run_anime_notifications --limit=10
   
   # Or run individual tasks
   python manage.py run_anime_notifications --skip-send --skip-cleanup  # Only schedule
   python manage.py run_anime_notifications --skip-schedule --skip-cleanup  # Only send
   ```

4. **View task logs:**
   - Vào **Files** tab → `/var/log/`
   - Check file logs để debug nếu có lỗi

## Testing Locally

### Test combined command:

```bash
# Test all tasks together
python manage.py run_anime_notifications --limit=5

# Test specific tasks only
python manage.py run_anime_notifications --skip-send --skip-cleanup  # Only schedule
python manage.py run_anime_notifications --skip-schedule --skip-cleanup  # Only send
python manage.py run_anime_notifications --skip-schedule --skip-send  # Only cleanup
```

### Test individual commands (nếu cần):

```bash
# Test schedule
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
    notify_email='your_email@gmail.com'  # Set email to enable notifications
)
```

2. **Set notification preferences (optional - có defaults):**
```bash
curl -X PUT http://localhost:8000/api/notification/preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notify_before_hours": 24, "enabled": true, "notify_by_email": true}'
```

3. **Run all notification tasks:**
```bash
python manage.py run_anime_notifications
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

# Xem notification task logs  
grep "Starting Anime Notification Tasks" ~/MyAnilist/logs/django.log
grep "All tasks completed" ~/MyAnilist/logs/django.log
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
python manage.py run_anime_notifications --limit=5
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

- ✅ Check user có follow anime với `notify_email` không rỗng (email address)
- ✅ Check user KHÔNG có preferences với `enabled=False` (nếu không có preference thì dùng default enabled=True)
- ✅ Check anime có `nextAiringEpisode` (anime finished thì không có)

### Notifications không được gửi:

- ✅ Check email settings trong `settings.py`
- ✅ Test email manually: `python manage.py shell` → call `MailService`
- ✅ Check `notify_at` <= current time

### Duplicate notifications:

- Model có `unique_together = ['user', 'anilist_id', 'episode_number']`
- Không thể tạo duplicate

## Best Practices

### 1. Chạy 1 lần/ngày là đủ:
- Command gom cả 3 tasks: schedule → send → cleanup
- Với PythonAnywhere Free (1 task limit), chạy daily at 12:00 UTC
- Nếu cần realtime hơn, upgrade Hacker plan và tách riêng tasks

### 2. Monitor performance:
```bash
# Check execution time
grep "All tasks completed" ~/MyAnilist/logs/django.log | tail -20

# Check how many notifications scheduled/sent
grep "notifications scheduled" ~/MyAnilist/logs/django.log | tail -10
grep "Successfully sent" ~/MyAnilist/logs/django.log | tail -10
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
