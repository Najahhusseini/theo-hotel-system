# test_roles.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login(username, password):
    """Login and return token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_endpoint(token, endpoint, method="GET", data=None):
    """Test an endpoint with authentication"""
    headers = {"Authorization": f"Bearer {token}"}
    
    if method == "GET":
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    elif method == "POST":
        response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
    elif method == "PUT":
        response = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers)
    elif method == "DELETE":
        response = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)
    
    return response.status_code

def test_role_permissions():
    """Test what each role can do"""
    
    # Define users and their expected permissions
    users = {
        "admin": {"password": "Admin123!", "role": "super_admin"},
        "manager": {"password": "Manager123!", "role": "hotel_manager"},
        "frontdesk": {"password": "Front123!", "role": "front_desk"},
        "housekeeping": {"password": "House123!", "role": "housekeeping"},
        "maintenance": {"password": "Maint123!", "role": "maintenance"},
        "accounting": {"password": "Acct123!", "role": "accounting"}
    }
    
    # Define endpoints and expected access (200 = allowed, 403 = denied)
    endpoints = {
        "GET /hotels/": {"description": "View hotels", "expected_for": ["admin", "manager", "frontdesk"]},
        "POST /hotels/": {"description": "Create hotel", "expected_for": ["admin", "manager"]},
        "DELETE /hotels/1": {"description": "Delete hotel", "expected_for": ["admin"]},
        
        "GET /rooms/": {"description": "View rooms", "expected_for": ["admin", "manager", "frontdesk", "housekeeping"]},
        "PUT /rooms/1/status": {"description": "Update room status", "expected_for": ["admin", "manager", "housekeeping"]},
        
        "GET /guests/": {"description": "View guests", "expected_for": ["admin", "manager", "frontdesk"]},
        "POST /guests/": {"description": "Create guest", "expected_for": ["admin", "manager", "frontdesk"]},
        
        "GET /reservations/": {"description": "View reservations", "expected_for": ["admin", "manager", "frontdesk"]},
        "POST /reservations/": {"description": "Create reservation", "expected_for": ["admin", "manager", "frontdesk"]},
        "POST /reservations/1/check-in": {"description": "Check-in guest", "expected_for": ["admin", "manager", "frontdesk"]},
        "POST /reservations/1/check-out": {"description": "Check-out guest", "expected_for": ["admin", "manager", "frontdesk"]},
        
        "GET /auth/users/": {"description": "View users", "expected_for": ["admin", "manager"]},
        "POST /auth/register": {"description": "Create user", "expected_for": ["admin"]},
        
        "GET /auth/me": {"description": "View own profile", "expected_for": ["admin", "manager", "frontdesk", "housekeeping", "maintenance", "accounting"]}
    }
    
    print("\n" + "="*80)
    print("🔐 THEO ROLE-BASED ACCESS CONTROL TEST")
    print("="*80)
    
    # First, test each user's login
    print("\n📋 LOGIN TEST")
    print("-"*40)
    tokens = {}
    for username, info in users.items():
        token = login(username, info["password"])
        if token:
            print(f"✅ {username} ({info['role']}) - Login successful")
            tokens[username] = token
        else:
            print(f"❌ {username} - Login failed")
    
    # Now test each endpoint for each user
    print("\n" + "="*80)
    print("🎯 PERMISSION MATRIX")
    print("="*80)
    
    # Print header
    print(f"\n{'Endpoint':<45}", end="")
    for user in users.keys():
        print(f"{user:<12}", end="")
    print()
    print("-"*80)
    
    results = {}
    
    for endpoint, info in endpoints.items():
        print(f"{info['description']:<45}", end="")
        
        for username, info_user in users.items():
            if username in tokens:
                status = test_endpoint(tokens[username], endpoint)
                expected_allowed = username in info['expected_for']
                
                if expected_allowed and status == 200:
                    print(f"✅{'':<11}", end="")
                    results.setdefault(username, {"passed": 0, "failed": 0})
                    results[username]["passed"] += 1
                elif not expected_allowed and status == 403:
                    print(f"⛔{'':<11}", end="")
                    results.setdefault(username, {"passed": 0, "failed": 0})
                    results[username]["passed"] += 1
                else:
                    print(f"❌{'':<11}", end="")
                    results.setdefault(username, {"passed": 0, "failed": 0})
                    results[username]["failed"] += 1
            else:
                print(f"🔒{'':<11}", end="")
        
        print()
    
    # Summary
    print("\n" + "="*80)
    print("📊 PERMISSION TEST SUMMARY")
    print("="*80)
    
    for username, stats in results.items():
        total = stats["passed"] + stats["failed"]
        print(f"\n{username.upper()}:")
        print(f"   ✅ Passed: {stats['passed']}/{total}")
        print(f"   ❌ Failed: {stats['failed']}/{total}")
        if stats["failed"] == 0:
            print(f"   🎉 Perfect! All permissions correctly configured!")
    
    print("\n" + "="*80)
    print("✅ ROLE-BASED ACCESS TEST COMPLETED")
    print("="*80)

if __name__ == "__main__":
    print("\n🚀 Starting Role-Based Access Control Test...")
    print("⚠️  Make sure the server is running!\n")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            test_role_permissions()
        else:
            print("❌ Server is not responding correctly!")
    except:
        print("❌ Server is not running!")
        print("\nPlease start the server first:")
        print("  cd C:\\Users\\Najah\\THEO_v1\\backend")
        print("  venv\\Scripts\\activate")
        print("  uvicorn main:app --reload")