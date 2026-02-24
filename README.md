# Anime Image Service

A high-performance FastAPI service for uploading, processing, and serving anime images with automatic multi-resolution optimization (TMDB-style).

## Features

- 📸 **Image Upload & Processing**: Upload images and automatically generate 3 optimized resolutions
- 📋 **Resolution Tiers**: Generates w1280 (full), w780 (medium), and w300 (thumbnail)
- 💾 **SQLite Database**: Tracks all uploads with metadata
- 🔐 **API Key Authentication**: Secure endpoints with API key header
- 🚀 **Production Ready**: Includes health checks, static file serving, and proper error handling
- 📊 **Image Metadata**: Tracks original filename, dimensions, upload timestamp, and file sizes
- ☁️ **Google Drive Backup**: Automatic backup of database and uploads to Google Drive

## API Endpoints

### Upload Image
```
POST /upload
Header: x-api-key: your_api_key
Body: file (multipart/form-data)
```
Returns file_id and URLs for all resolutions.

### List All Images
```
GET /list
Header: x-api-key: your_api_key
```
Returns all uploaded images with metadata.

### Get Image Details
```
GET /images/{file_id}
Header: x-api-key: your_api_key
```
Returns metadata and URLs for a specific image.

### Delete Image
```
DELETE /images/{file_id}
Header: x-api-key: your_api_key
```
Deletes image and all variants from disk and database.

### Backup Endpoints (Optional - requires Google Drive setup)

#### Full Backup
```
POST /backup/full
Header: x-api-key: your_api_key
```
Backup both database and uploads directory to Google Drive.

#### Backup Database
```
POST /backup/database
Header: x-api-key: your_api_key
```
Backup only the database.

#### Backup Uploads
```
POST /backup/uploads
Header: x-api-key: your_api_key
```
Backup uploads directory as ZIP to Google Drive.

#### List Backups
```
GET /backup/list?limit=10
Header: x-api-key: your_api_key
```
List all backups from Google Drive.

#### Delete Backup
```
DELETE /backup/{file_id}
Header: x-api-key: your_api_key
```
Delete a backup from Google Drive.

#### Restore Database
```
POST /restore/database/{file_id}
Header: x-api-key: your_api_key
```
Restore database from Google Drive backup. Creates backup of current database first.

#### Restore Uploads
```
POST /restore/uploads/{file_id}
Header: x-api-key: your_api_key
```
Restore uploads directory from Google Drive backup. Creates backup of current uploads first.

#### Download Backup
```
GET /restore/download/{file_id}?destination=path
Header: x-api-key: your_api_key
```
Download a backup file from Google Drive to local path.

### Health Check
```
GET /health
```
Returns service status.

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd Image-service
```

2. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development

### Run Locally
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Change API Key
Edit `app/main.py` and update:
```python
API_KEY = "your_secure_key_here"
```

### Setup Google Drive Backups (Optional)

1. Follow [BACKUP_SETUP.md](BACKUP_SETUP.md) for detailed Google Drive configuration
2. Place `google-credentials.json` in project root
3. Add to `.env`:
   ```
   GOOGLE_DRIVE_CREDENTIALS=google-credentials.json
   GOOGLE_DRIVE_FOLDER_ID=  # Optional
   ```
4. Test backup endpoint:
   ```bash
   curl -X POST http://localhost:8000/backup/full \
     -H "x-api-key: this_is_random_key"
   ```

## Production Deployment

### Option 1: Using Gunicorn (Recommended)

1. Install gunicorn:
```bash
pip install gunicorn
```

2. Run:
```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Option 2: Using Docker

1. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY app ./app
COPY uploads ./uploads

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

2. Build and run:
```bash
docker build -t anime-image-service .
docker run -p 8000:8000 -v uploads:/app/uploads anime-image-service
```

### Option 3: Using Systemd (Linux)

1. Create service file `/etc/systemd/system/anime-image.service`:
```ini
[Unit]
Description=Anime Image Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/anime-image-service
ExecStart=/opt/anime-image-service/venv/bin/gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable anime-image
sudo systemctl start anime-image
```

### Option 4: Using Nginx Reverse Proxy

1. Install Nginx and configure `/etc/nginx/sites-available/anime-image`:
```nginx
upstream anime_image {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 100M;

    location / {
        proxy_pass http://anime_image;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        alias /opt/anime-image-service/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

2. Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/anime-image /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Environment Variables

Create `.env` file for production:
```
API_KEY=your_super_secret_key_here
UPLOAD_DIR=uploads
DB_PATH=images.db
```

Update `app/main.py` to read from environment:
```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY", "this_is_random_key")
```

## Database

The service uses SQLite with auto-initialization. Database file: `images.db`

### Schema
```sql
CREATE TABLE images (
    id TEXT PRIMARY KEY,
    original_filename TEXT,
    uploaded_at TIMESTAMP,
    original_width INTEGER,
    original_height INTEGER,
    file_sizes TEXT
)
```

### Backup
```bash
cp images.db images.db.backup
```

## Performance Tips

1. **Enable compression** in Nginx:
```nginx
gzip on;
gzip_types image/webp text/plain application/json;
```

2. **Use CDN** for `/uploads/` directory to cache images globally

3. **Monitor disk space** for uploads directory

4. **Consider adding cleanup job** to remove old images:
```python
# Run periodically with cron
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('images.db')
c = conn.cursor()
old_date = (datetime.now() - timedelta(days=30)).isoformat()
c.execute("SELECT id FROM images WHERE uploaded_at < ?", (old_date,))
# Delete files and records
```

## Testing

```bash
# Test upload
curl -X POST http://localhost:8000/upload \
  -H "x-api-key: this_is_random_key" \
  -F "file=@test_image.jpg"

# Test list
curl http://localhost:8000/list \
  -H "x-api-key: this_is_random_key"
```

## Troubleshooting

### Permission Denied on uploads/
```bash
chmod -R 755 uploads/
```

### Database locked
Stop all running instances before backup/restore.

### High memory usage
- Limit worker count in gunicorn
- Implement image size limits in upload endpoint

## License

MIT

## Support

For issues, create a GitHub issue with:
- API request/response
- File size and dimensions
- Error message and logs
