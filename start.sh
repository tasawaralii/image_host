#!/bin/bash

# Anime Image Service - Production Startup Script

set -e

echo "🚀 Starting Anime Image Service..."

# Check Python version
python_version=$(python3 --version)
echo "✓ Python: $python_version"

# Create uploads directory
mkdir -p uploads/{w1280,w780,w300}
echo "✓ Upload directories created"

# Install dependencies
if [ -f "requirements-prod.txt" ]; then
    echo "📦 Installing production dependencies..."
    pip install -q -r requirements-prod.txt
else
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
    pip install -q gunicorn
fi

# Run migrations/setup if needed
echo "🛠️  Initializing database..."
python3 -c "from app.main import init_db; init_db()"

# Set permissions
chmod -R 755 uploads/

echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting service with gunicorn (4 workers)..."
echo "📍 Service will be available at: http://localhost:8000"
echo "📚 API docs available at: http://localhost:8000/docs"
echo ""

exec gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
