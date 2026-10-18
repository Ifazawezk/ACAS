#!/usr/bin/env python
"""
JWT Authentication Test Script
Verifies that the ACAS system correctly validates JWT tokens
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8001"
TEST_CREDENTIALS = {
    "username": "admin",
    "password": "admin@123"
}

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_login():
    """Test 1: Login and get JWT token"""
    print_section("TEST 1: Login (Get JWT Token)")
    
    response = requests.post(
        f"{BASE_URL}/auth/token",
        json=TEST_CREDENTIALS,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Request: POST /auth/token")
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAILED: Login failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ SUCCESS: Login successful")
    print(f"\nResponse:")
    print(f"  - Token Type: {data.get('token_type')}")
    print(f"  - User ID: {data.get('user_id')}")
    print(f"  - Username: {data.get('username')}")
    print(f"  - Role: {data.get('role')}")
    print(f"  - Token (truncated): {data.get('access_token')[:50]}...")
    
    return data.get('access_token')

def test_protected_route_with_token(token):
    """Test 2: Access protected endpoint WITH valid JWT"""
    print_section("TEST 2: Access Protected Route (WITH JWT)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/comments?limit=5",
        headers=headers
    )
    
    print(f"Request: GET /comments")
    print(f"Headers: Authorization: Bearer <token>")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Protected route accessible with JWT")
        print(f"  - Comments returned: {len(data) if isinstance(data, list) else 'N/A'}")
        return True
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return False

def test_protected_route_without_token():
    """Test 3: Access protected endpoint WITHOUT JWT (should fail)"""
    print_section("TEST 3: Access Protected Route (WITHOUT JWT)")
    
    response = requests.get(
        f"{BASE_URL}/comments?limit=5",
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Request: GET /comments")
    print(f"Headers: (No Authorization header)")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 403 or response.status_code == 401:
        print(f"✅ SUCCESS: Protected route properly rejects request without JWT")
        print(f"  - Status code: {response.status_code} (Unauthorized)")
        return True
    else:
        print(f"❌ FAILED: Expected 401/403 but got {response.status_code}")
        return False

def test_invalid_token():
    """Test 4: Try with invalid JWT token"""
    print_section("TEST 4: Access Protected Route (WITH INVALID JWT)")
    
    headers = {
        "Authorization": "Bearer invalid.token.here",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/comments?limit=5",
        headers=headers
    )
    
    print(f"Request: GET /comments")
    print(f"Headers: Authorization: Bearer invalid.token.here")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✅ SUCCESS: Protected route properly rejects invalid JWT")
        print(f"  - Status code: 401 (Unauthorized)")
        return True
    else:
        print(f"❌ FAILED: Expected 401 but got {response.status_code}")
        return False

def test_get_user_info(token):
    """Test 5: Get current user info via /auth/me"""
    print_section("TEST 5: Get Current User Info (/auth/me)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=headers
    )
    
    print(f"Request: GET /auth/me")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: User info retrieved successfully")
        print(f"\nUser Information:")
        print(f"  - ID: {data.get('id')}")
        print(f"  - Username: {data.get('username')}")
        print(f"  - Email: {data.get('email')}")
        print(f"  - Role: {data.get('role')}")
        print(f"  - Is Active: {data.get('is_active')}")
        return True
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        return False

def main():
    print("\n" + "="*60)
    print("  ACAS JWT Authentication Test Suite")
    print("  Testing: Cookie-Free JWT Authentication")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ Server health check failed!")
            print(f"Status: {response.status_code}")
            print("Make sure the server is running on port 8001")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server on port 8001")
        print("Make sure the server is running: python start_server.py")
        sys.exit(1)
    
    print("\n✅ Server is running")
    
    # Run tests
    results = {}
    
    # Test 1: Login
    token = test_login()
    results["Login"] = token is not None
    
    if not token:
        print("\n❌ Cannot continue without valid token")
        sys.exit(1)
    
    # Test 2: Protected route with token
    results["Protected Route (With JWT)"] = test_protected_route_with_token(token)
    
    # Test 3: Protected route without token
    results["Protected Route (Without JWT)"] = test_protected_route_without_token()
    
    # Test 4: Invalid token
    results["Protected Route (Invalid JWT)"] = test_invalid_token()
    
    # Test 5: Get user info
    results["Get User Info"] = test_get_user_info(token)
    
    # Summary
    print_section("TEST SUMMARY")
    print()
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print()
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All JWT authentication tests passed!")
        print("✅ Cookie-free JWT authentication is working correctly")
        return 0
    else:
        print(f"\n❌ {total_tests - passed_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
