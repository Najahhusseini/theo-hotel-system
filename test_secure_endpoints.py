# test_secure_endpoints.py
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_unauthenticated_access():
    """Test accessing endpoints without authentication"""
    print("\n" + "="*50)
    print("🔓 TESTING UNAUTHENTICATED ACCESS")
    print("="*50)
    
    endpoints = [
        "/hotels/",
        "/rooms/",
        "/guests/",
        "/reservations/"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"GET {endpoint}: {response.status_code}")
        if response.status_code in [401, 403]:
            print(f"  ✅ Properly blocked")
        else:
            print(f"  ❌ Should be blocked!")

def test_authenticated_access():
    """Test accessing endpoints with valid authentication"""
    print("\n" + "="*50)
    print("🔐 TESTING AUTHENTICATED ACCESS")
    print("="*50)
    
    # Login as front desk
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "frontdesk",
        "password": "Front123!"
    })
    
    if login_response.status_code != 200:
        print("❌ Login failed!")
        return
    
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in as frontdesk")
    
    # Test endpoints
    endpoints = [
        ("GET", "/hotels/"),
        ("GET", "/rooms/"),
        ("GET", "/guests/"),
        ("GET", "/reservations/"),
        ("GET", "/auth/me")
    ]
    
    for method, endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"{method} {endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ Access granted")
        else:
            print(f"  ❌ Access denied unexpectedly")

def test_role_permissions():
    """Test role-specific permissions"""
    print("\n" + "="*50)
    print("👥 TESTING ROLE PERMISSIONS")
    print("="*50)
    
    users = [
        ("frontdesk", "Front123!", "Front Desk"),
        ("housekeeping", "House123!", "Housekeeping"),
        ("manager", "Manager123!", "Manager")
    ]
    
    for username, password, role in users:
        # Login
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        
        if login_response.status_code != 200:
            print(f"❌ {role} login failed!")
            continue
        
        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"\n📋 {role} ({username}):")
        
        # Test what they can access
        if role == "Housekeeping":
            # Should access rooms but not reservations
            rooms_response = requests.get(f"{BASE_URL}/rooms/", headers=headers)
            print(f"  View rooms: {rooms_response.status_code}")
            
            reservations_response = requests.get(f"{BASE_URL}/reservations/", headers=headers)
            print(f"  View reservations: {reservations_response.status_code}")
            
        elif role == "Front Desk":
            # Should access most things
            endpoints = ["/hotels/", "/rooms/", "/guests/", "/reservations/"]
            for endpoint in endpoints:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                print(f"  View {endpoint}: {response.status_code}")

def run_tests():
    print("\n" + "🔒"*15)
    print("   THEO SECURITY TEST SUITE")
    print("🔒"*15)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server not responding!")
            return
        print("✅ Server is running")
    except:
        print("❌ Server is not running!")
        return
    
    test_unauthenticated_access()
    test_authenticated_access()
    test_role_permissions()
    
    print("\n" + "🎉"*15)
    print("   SECURITY TESTS COMPLETED!")
    print("🎉"*15)

if __name__ == "__main__":
    run_tests()