#!/usr/bin/env python3
"""
Test script for the admin-verified staff creation functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_verification():
    """Test admin password verification"""
    print("=== Testing Admin Password Verification ===")
    
    url = f"{BASE_URL}/staff/verify-password/"
    data = {
        "admin_password": "root"
    }
    
    response = requests.post(url, 
                           data=json.dumps(data),
                           headers={'Content-Type': 'application/json'})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.json().get('success', False)

def test_staff_creation():
    """Test staff user creation"""
    print("\n=== Testing Staff User Creation ===")
    
    url = f"{BASE_URL}/staff/create-account/"
    data = {
        "admin_password": "root",
        "user_type": "moderator",
        "username": "test_moderator_123",
        "email": "test_moderator_123@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "Moderator",
        "phone_number": "1234567890"
    }
    
    # Get CSRF token first
    session = requests.Session()
    csrf_url = f"{BASE_URL}/staff/create-user/"
    csrf_response = session.get(csrf_url)
    
    # Extract CSRF token from cookies
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == 'csrftoken':
            csrf_token = cookie.value
            break
    
    headers = {}
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    
    response = session.post(url, data=data, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.json().get('success', False)

if __name__ == "__main__":
    # Test admin verification
    admin_verified = test_admin_verification()
    
    if admin_verified:
        print("✅ Admin verification successful")
        
        # Test staff creation
        staff_created = test_staff_creation()
        
        if staff_created:
            print("✅ Staff creation successful")
        else:
            print("❌ Staff creation failed")
    else:
        print("❌ Admin verification failed")
