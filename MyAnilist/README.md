# MyAnilist Django Project

## Cài đặt và Migration Database

### Yêu cầu trước khi bắt đầu:
1. MySQL Server đã được cài đặt và đang chạy
2. Python 3.8+ đã được cài đặt

### Bước 1: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 2: Cấu hình Database
1. Cập nhật file `.env` trong thư mục `MyAnilist` với thông tin MySQL của bạn:
```env
DB_NAME=myanilist_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=your-generated-secret-key-here
DEBUG=True
```

2. Tạo database trong MySQL:
```sql
CREATE DATABASE myanilist_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Bước 3: Tạo và áp dụng migrations
```bash
# Di chuyển đến thư mục project
cd MyAnilist

# Tạo migrations cho các model
python manage.py makemigrations

# Áp dụng migrations lên database
python manage.py migrate

# Tạo superuser (tuỳ chọn)
python manage.py createsuperuser
```

### Bước 4: Chạy server
```bash
python manage.py runserver
```

## Cấu trúc Database

### Models được định nghĩa:
- **User**: Thông tin người dùng
- **AnimeFollow**: Tình trạng theo dõi anime
- **History**: Lịch sử xem phim
- **NotificationLog**: Log thông báo
- **List**: Danh sách anime
- **UserList**: Quan hệ user-list
- **AnimeList**: Quan hệ list-anime

## Troubleshooting

### Lỗi kết nối MySQL:
1. Kiểm tra MySQL service đang chạy
2. Kiểm tra username/password trong `.env`
3. Đảm bảo database đã được tạo

### Lỗi mysqlclient:
Trên Windows, có thể cần cài đặt Visual C++ Build Tools hoặc sử dụng:
```bash
pip install PyMySQL
```
Sau đó thêm vào `__init__.py` của project:
```python
import pymysql
pymysql.install_as_MySQLdb()
```