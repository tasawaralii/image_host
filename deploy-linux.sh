#!/bin/bash

# Anime Image Service - Linux Deployment Setup Script
# Run this on your Linux server to deploy the application

set -e

echo "📦 Anime Image Service - Linux Deployment Setup"
echo "==============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Configuration
APP_DIR="/opt/anime-image-service"
APP_USER="www-data"
LOG_DIR="/var/log/anime-image"

echo "1️⃣  Creating application directory..."
mkdir -p "$APP_DIR"
mkdir -p "$LOG_DIR"
cd "$APP_DIR"

echo "2️⃣  Creating uploads directory..."
mkdir -p uploads/{w1280,w780,w300}

echo "3️⃣  Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "4️⃣  Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-prod.txt

echo "5️⃣  Setting up permissions..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$LOG_DIR"
chmod 755 "$APP_DIR"
chmod 755 "$LOG_DIR"

echo "6️⃣  Setting up systemd service..."
cp anime-image.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable anime-image.service

echo "7️⃣  Setting up Nginx reverse proxy..."
cp nginx.conf.example /etc/nginx/sites-available/anime-image 2>/dev/null || echo "Note: Manually copy nginx.conf to /etc/nginx/sites-available/anime-image"
ln -sf /etc/nginx/sites-available/anime-image /etc/nginx/sites-enabled/anime-image 2>/dev/null || true
nginx -t && systemctl restart nginx 2>/dev/null || echo "Note: Nginx configuration needs manual setup"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure API key in $APP_DIR/.env"
echo "2. Start service: sudo systemctl start anime-image"
echo "3. Check status: sudo systemctl status anime-image"
echo "4. View logs: sudo journalctl -u anime-image -f"
echo "5. Configure domain in Nginx and setup SSL (certbot)"
echo ""
echo "📚 Useful commands:"
echo "  - Start:   sudo systemctl start anime-image"
echo "  - Stop:    sudo systemctl stop anime-image"
echo "  - Restart: sudo systemctl restart anime-image"
echo "  - Logs:    sudo journalctl -u anime-image -f"
echo "  - Status:  sudo systemctl status anime-image"
echo ""
