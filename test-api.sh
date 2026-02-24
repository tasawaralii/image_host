#!/bin/bash
# Anime Image Service - Testing Script
# Tests all API endpoints

set -e

API_KEY="this_is_random_key"
BASE_URL="http://localhost:8000"
TEST_IMAGE="test.jpg"

echo "🧪 Anime Image Service - API Testing"
echo "===================================="
echo ""

# Check if server is running
echo "1️⃣  Checking server health..."
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo "❌ Server not responding. Make sure it's running:"
    echo "   uvicorn app.main:app --reload"
    exit 1
fi
echo "✅ Server is healthy"
echo ""

# Create test image if it doesn't exist
if [ ! -f "$TEST_IMAGE" ]; then
    echo "2️⃣  Creating test image..."
    python3 -c "
from PIL import Image
img = Image.new('RGB', (2400, 3200), color='blue')
img.save('test.jpg')
"
    echo "✅ Test image created (test.jpg)"
else
    echo "2️⃣  Using existing test image"
fi
echo ""

# Test upload
echo "3️⃣  Testing upload endpoint..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/upload" \
    -H "x-api-key: $API_KEY" \
    -F "file=@$TEST_IMAGE")

FILE_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['file_id'])")

if [ -z "$FILE_ID" ]; then
    echo "❌ Upload failed"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

echo "✅ Upload successful"
echo "   File ID: $FILE_ID"
echo ""

# Test list endpoint
echo "4️⃣  Testing list endpoint..."
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/list" \
    -H "x-api-key: $API_KEY")

TOTAL=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")

if [ -z "$TOTAL" ]; then
    echo "❌ List failed"
    exit 1
fi

echo "✅ List successful"
echo "   Total images: $TOTAL"
echo ""

# Test get image endpoint
echo "5️⃣  Testing get image endpoint..."
GET_RESPONSE=$(curl -s -X GET "$BASE_URL/images/$FILE_ID" \
    -H "x-api-key: $API_KEY")

if echo "$GET_RESPONSE" | grep -q "file_id"; then
    echo "✅ Get image successful"
    echo "$GET_RESPONSE" | python3 -m json.tool | head -20
else
    echo "❌ Get image failed"
    exit 1
fi
echo ""

# Test image downloads
echo "6️⃣  Testing image serving..."
for res in w1280 w780 w300; do
    URL="$BASE_URL/uploads/$res/$FILE_ID"
    SIZE=$(curl -s -I "$URL" | grep -i content-length | awk '{print $2}' | tr -d '\r')
    if [ ! -z "$SIZE" ]; then
        echo "✅ $res image: ${SIZE}B"
    else
        echo "❌ $res image: Failed to get"
    fi
done
echo ""

# Test delete endpoint
echo "7️⃣  Testing delete endpoint..."
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/images/$FILE_ID" \
    -H "x-api-key: $API_KEY")

if echo "$DELETE_RESPONSE" | grep -q "deleted"; then
    echo "✅ Delete successful"
else
    echo "❌ Delete failed"
    exit 1
fi
echo ""

# Verify deletion
echo "8️⃣  Verifying deletion..."
GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/images/$FILE_ID" \
    -H "x-api-key: $API_KEY")

HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" == "404" ]; then
    echo "✅ Image successfully deleted"
else
    echo "❌ Image still exists or error occurred (HTTP $HTTP_CODE)"
fi
echo ""

# Test auth
echo "9️⃣  Testing authentication..."
AUTH_RESPONSE=$(curl -s -X GET "$BASE_URL/list" \
    -H "x-api-key: wrong_key" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" == "403" ]; then
    echo "✅ Authentication working correctly"
else
    echo "❌ Authentication bypass (HTTP $HTTP_CODE)"
fi
echo ""

echo "🎉 All tests passed!"
echo ""
echo "📚 Next steps:"
echo "1. Visit $BASE_URL/docs for interactive API documentation"
echo "2. Read README.md for deployment guides"
echo "3. Update API_KEY in production (.env file)"
echo "4. Test with real images from your application"
