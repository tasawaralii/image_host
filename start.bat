@echo off
REM Anime Image Service - Production Startup Script (Windows)

echo 🚀 Starting Anime Image Service...

REM Check Python version
python --version
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)
echo ✓ Python found

REM Create uploads directory
if not exist "uploads\w1280" mkdir uploads\w1280
if not exist "uploads\w780" mkdir uploads\w780
if not exist "uploads\w300" mkdir uploads\w300
echo ✓ Upload directories created

REM Install dependencies
echo 📦 Installing production dependencies...
if exist "requirements-prod.txt" (
    pip install -q -r requirements-prod.txt
) else (
    pip install -q -r requirements.txt
    pip install -q gunicorn
)

REM Initialize database
echo 🛠️  Initializing database...
python -c "from app.main import init_db; init_db()"

echo.
echo ✅ Setup complete!
echo.
echo Starting service with uvicorn...
echo 📍 Service will be available at: http://localhost:8000
echo 📚 API docs available at: http://localhost:8000/docs
echo.

REM For production on Windows, use:
REM uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
