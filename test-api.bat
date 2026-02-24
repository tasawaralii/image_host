@echo off
REM Anime Image Service - Testing Script (Windows)
REM Tests all API endpoints

setlocal enabledelayedexpansion

set API_KEY=this_is_random_key
set BASE_URL=http://localhost:8000
set TEST_IMAGE=test.jpg

echo 🧪 Anime Image Service - API Testing
echo ====================================
echo.

REM Check if server is running
echo 1️⃣  Checking server health...
curl -s "%BASE_URL%/health" > nul
if errorlevel 1 (
    echo ❌ Server not responding. Make sure it's running:
    echo    python -m uvicorn app.main:app --reload
    exit /b 1
)
echo ✅ Server is healthy
echo.

REM Create test image if it doesn't exist
if not exist "%TEST_IMAGE%" (
    echo 2️⃣  Creating test image...
    python -c "from PIL import Image; Image.new('RGB', (2400, 3200), color='blue').save('test.jpg')"
    echo ✅ Test image created
) else (
    echo 2️⃣  Using existing test image
)
echo.

REM Test upload
echo 3️⃣  Testing upload endpoint...
for /f "tokens=*" %%A in ('curl -s -X POST "%BASE_URL%/upload" -H "x-api-key: %API_KEY%" -F "file=@%TEST_IMAGE%" ^| python -c "import sys, json; d=json.load(sys.stdin); print(d.get('file_id', ''))"') do (
    set FILE_ID=%%A
)

if "!FILE_ID!"=="" (
    echo ❌ Upload failed
    exit /b 1
)

echo ✅ Upload successful
echo    File ID: !FILE_ID!
echo.

REM Test list endpoint
echo 4️⃣  Testing list endpoint...
curl -s -X GET "%BASE_URL%/list" -H "x-api-key: %API_KEY%" | python -m json.tool > nul
if errorlevel 1 (
    echo ❌ List failed
    exit /b 1
)
echo ✅ List successful
echo.

REM Test get image endpoint
echo 5️⃣  Testing get image endpoint...
curl -s -X GET "%BASE_URL%/images/!FILE_ID!" -H "x-api-key: %API_KEY%" | python -m json.tool | findstr /C:"file_id" > nul
if errorlevel 1 (
    echo ❌ Get image failed
    exit /b 1
)
echo ✅ Get image successful
echo.

REM Test image serving
echo 6️⃣  Testing image serving...
for %%R in (w1280 w780 w300) do (
    curl -s -I "%BASE_URL%/uploads/%%R/!FILE_ID!" | findstr /C:"200" > nul
    if errorlevel 0 (
        echo ✅ %%R image accessible
    )
)
echo.

REM Test delete endpoint
echo 7️⃣  Testing delete endpoint...
curl -s -X DELETE "%BASE_URL%/images/!FILE_ID!" -H "x-api-key: %API_KEY%" | findstr /C:"deleted" > nul
if errorlevel 1 (
    echo ❌ Delete failed
    exit /b 1
)
echo ✅ Delete successful
echo.

REM Test auth
echo 8️⃣  Testing authentication...
curl -s -X GET "%BASE_URL%/list" -H "x-api-key: wrong_key" | findstr /C:"Invalid API Key" > nul
if errorlevel 0 (
    echo ✅ Authentication working correctly
)
echo.

echo 🎉 All tests passed!
echo.
echo 📚 Next steps:
echo 1. Visit %BASE_URL%/docs for interactive API documentation
echo 2. Read README.md for deployment guides
echo 3. Update API_KEY in production (.env file)
echo.

pause
