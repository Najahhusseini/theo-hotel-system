# test_auth.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    """Test login endpoint"""
    print("\n" + "="*50)
    print("🔐 TESTING LOGIN")
    print("="*50)
    
    login_data = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"   Token: {data['access_token'][:50]}...")
        print(f"   User: {data['user']['username']} ({data['user']['role']})")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def test_get_me(token):
    """Test getting current user info"""
    print("\n" + "="*50)
    print("👤 GETTING USER INFO")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        user = response.json()
        print("✅ User info retrieved!")
        print(f"   Username: {user['username']}")
        print(f"   Name: {user['first_name']} {user['last_name']}")
        print(f"   Role: {user['role']}")
        print(f"   Email: {user['email']}")
    else:
        print(f"❌ Failed: {response.json()}")

def test_protected_endpoint(token):
    """Test accessing a protected endpoint"""
    print("\n" + "="*50)
    print("🛡️ TESTING PROTECTED ENDPOINT")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/hotels/", headers=headers)
    
    if response.status_code == 200:
        print("✅ Successfully accessed protected endpoint!")
        print(f"   Found {len(response.json())} hotels")
    else:
        print(f"❌ Failed: {response.status_code} - {response.json()}")

def test_invalid_token():
    """Test with invalid token"""
    print("\n" + "="*50)
    print("❌ TESTING INVALID TOKEN")
    print("="*50)
    
    headers = {"Authorization": "Bearer invalid-token-123"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 401:
        print("✅ Correctly rejected invalid token (401 Unauthorized)")
    else:
        print(f"⚠️ Unexpected response: {response.status_code}")

def test_no_token():
    """Test without token"""
    print("\n" + "="*50)
    print("🚫 TESTING NO TOKEN")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/auth/me")
    
    if response.status_code == 403 or response.status_code == 401:
        print("✅ Correctly rejected request without token")
    else:
        print(f"⚠️ Unexpected response: {response.status_code}")

def run_tests():
    print("\n" + "🔐"*15)
    print("   THEO AUTHENTICATION TEST SUITE")
    print("🔐"*15)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("⚠️ Server responded but health check failed")
    except:
        print("\n❌ ERROR: Server is not running!")
        print("Please start the server first:")
        print("  cd C:\\Users\\Najah\\THEO_v1\\backend")
        print("  venv\\Scripts\\activate")
        print("  uvicorn main:app --reload")
        return
    
    # Test without token
    test_no_token()
    
    # Test login
    token = test_login()
    
    if token:
        # Test getting user info
        test_get_me(token)
        
        # Test protected endpoint
        test_protected_endpoint(token)
    
    # Test invalid token
    test_invalid_token()
    
    print("\n" + "🎉"*15)
    print("   AUTHENTICATION TESTS COMPLETED!")
    print("🎉"*15)

if __name__ == "__main__":
    run_tests()