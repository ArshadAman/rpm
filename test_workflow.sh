#!/bin/bash

# Test script to simulate the exact form submission workflow

echo "=== Testing Complete Staff Creation Workflow ==="

# Step 1: Get CSRF Token
echo "Step 1: Getting CSRF token..."
CSRF_TOKEN=$(curl -s -c cookies.txt http://localhost:8000/staff/create-user/ | grep -o 'name="csrfmiddlewaretoken" value="[^"]*"' | sed 's/.*value="\([^"]*\)".*/\1/')

if [ -z "$CSRF_TOKEN" ]; then
    echo "❌ Failed to get CSRF token"
    exit 1
fi

echo "✅ CSRF token obtained: ${CSRF_TOKEN:0:10}..."

# Step 2: Verify Admin Password
echo -e "\nStep 2: Verifying admin password..."
VERIFY_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -b cookies.txt \
    -d '{"admin_password": "root"}' \
    http://localhost:8000/staff/verify-password/)

echo "Verify Response: $VERIFY_RESPONSE"

if echo "$VERIFY_RESPONSE" | grep -q '"success": true'; then
    echo "✅ Admin password verified"
else
    echo "❌ Admin password verification failed"
    exit 1
fi

# Step 3: Create Staff User
echo -e "\nStep 3: Creating moderator account..."
CREATE_RESPONSE=$(curl -s -X POST \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -b cookies.txt \
    -F "admin_password=root" \
    -F "user_type=moderator" \
    -F "username=test_moderator_789" \
    -F "email=test_moderator_789@example.com" \
    -F "password=testpassword123" \
    -F "first_name=Test" \
    -F "last_name=Moderator789" \
    -F "phone_number=1234567890" \
    http://localhost:8000/staff/create-account/)

echo "Create Response: $CREATE_RESPONSE"

if echo "$CREATE_RESPONSE" | grep -q '"success": true'; then
    echo "✅ Moderator account created successfully!"
else
    echo "❌ Moderator account creation failed"
fi

# Cleanup
rm -f cookies.txt

echo -e "\n=== Test Complete ==="
