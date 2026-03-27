# test_housekeeping.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login(username, password):
    """Login helper"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def get_housekeeping_user_id(token):
    """Get the ID of the first housekeeping user"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get users from the API
    response = requests.get(f"{BASE_URL}/auth/users/", headers=headers)
    
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get('role') == 'housekeeping':
                print(f"  Found housekeeping user: {user['username']} (ID: {user['id']})")
                return user['id']
    
    # Fallback: direct database query via Python
    print("  Trying direct database query...")
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        
        db = SessionLocal()
        user = db.query(User).filter(User.role == 'housekeeping').first()
        db.close()
        
        if user:
            print(f"  Found housekeeping user via DB: {user.username} (ID: {user.id})")
            return user.id
    except Exception as e:
        print(f"  Database query failed: {e}")
    
    return None

def test_housekeeping_workflow():
    """Test the complete housekeeping workflow"""
    print("\n" + "🧹"*15)
    print("   THEO HOUSEKEEPING MODULE TEST")
    print("🧹"*15)
    
    # Login as manager to create tasks
    manager_token = login("manager", "Manager123!")
    if not manager_token:
        print("❌ Manager login failed!")
        return
    
    print("✅ Manager logged in")
    
    # Get housekeeping user ID
    print("\n🔍 Looking for housekeeping staff...")
    housekeeping_id = get_housekeeping_user_id(manager_token)
    if not housekeeping_id:
        print("❌ Could not find housekeeping user!")
        print("   Make sure you have a user with role 'housekeeping'")
        return
    
    print(f"✅ Housekeeping user ID: {housekeeping_id}")
    
    # First, check if there are any rooms
    print("\n🏨 Checking for rooms...")
    headers = {"Authorization": f"Bearer {manager_token}"}
    rooms_response = requests.get(f"{BASE_URL}/rooms/", headers=headers)
    
    if rooms_response.status_code == 200:
        rooms = rooms_response.json()
        if not rooms:
            print("❌ No rooms found! Please create a room first.")
            print("   Run: python setup_hotel_and_rooms.py")
            return
        print(f"✅ Found {len(rooms)} room(s)")
        # Use the first room's ID
        room_id = rooms[0]['id']
        hotel_id = rooms[0]['hotel_id']
        print(f"   Using Room ID: {room_id}, Hotel ID: {hotel_id}")
    else:
        print("❌ Could not get rooms")
        return
    
    # Create a housekeeping task
    print("\n📝 Creating housekeeping task...")
    task_data = {
        "task_type": "checkout_clean",
        "priority": "high",
        "room_id": room_id,
        "hotel_id": hotel_id,
        "notes": "VIP guest, please pay extra attention",
        "special_instructions": "Use premium amenities"
    }
    
    response = requests.post(
        f"{BASE_URL}/housekeeping/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    
    if response.status_code == 201:
        task = response.json()
        print(f"✅ Task created: {task['task_number']} (ID: {task['id']})")
        task_id = task['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Login as housekeeping staff
    housekeeping_token = login("housekeeping", "House123!")
    if not housekeeping_token:
        print("❌ Housekeeping login failed!")
        return
    
    print("✅ Housekeeping staff logged in")
    
    # Get tasks assigned (should be empty initially)
    print("\n📋 Getting assigned tasks...")
    response = requests.get(
        f"{BASE_URL}/housekeeping/tasks/my",
        headers={"Authorization": f"Bearer {housekeeping_token}"}
    )
    if response.status_code == 200:
        print(f"Tasks assigned: {len(response.json())}")
    else:
        print(f"Error: {response.status_code}")
    
    # Manager assigns task to housekeeping
    print("\n👥 Assigning task to housekeeping...")
    response = requests.put(
        f"{BASE_URL}/housekeeping/tasks/{task_id}/assign",
        json={"assigned_to_id": housekeeping_id},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    
    if response.status_code == 200:
        print("✅ Task assigned")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Housekeeping starts task
    print("\n🔨 Starting task...")
    response = requests.put(
        f"{BASE_URL}/housekeeping/tasks/{task_id}/start",
        headers={"Authorization": f"Bearer {housekeeping_token}"}
    )
    
    if response.status_code == 200:
        task = response.json()
        print(f"✅ Task started: {task['status']}")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Housekeeping completes task
    print("\n✅ Completing task...")
    response = requests.put(
        f"{BASE_URL}/housekeeping/tasks/{task_id}/complete",
        json={"supplies_used": "Cleaning supplies, towels, amenities", "notes": "All done!"},
        headers={"Authorization": f"Bearer {housekeeping_token}"}
    )
    
    if response.status_code == 200:
        task = response.json()
        print(f"✅ Task completed: {task['status']}")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Manager verifies task
    print("\n✓ Verifying task...")
    response = requests.put(
        f"{BASE_URL}/housekeeping/tasks/{task_id}/verify",
        json={"notes": "Great job!"},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    
    if response.status_code == 200:
        task = response.json()
        print(f"✅ Task verified: {task['status']}")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Check room status
    print("\n🏨 Checking room status...")
    response = requests.get(
        f"{BASE_URL}/rooms/{room_id}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    if response.status_code == 200:
        room = response.json()
        print(f"Room {room['room_number']} status: {room['status']}")
    
    # Get dashboard stats
    print("\n📊 Getting housekeeping stats...")
    response = requests.get(
        f"{BASE_URL}/housekeeping/stats",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    
    if response.status_code == 200:
        stats = response.json()
        print("\n🏨 Housekeeping Dashboard:")
        print("="*40)
        print(f"  Total Tasks:     {stats['total_tasks']}")
        print(f"  Pending:         {stats['pending']}")
        print(f"  In Progress:     {stats['in_progress']}")
        print(f"  Completed:       {stats['completed']}")
        print(f"  Verified:        {stats['verified']}")
        print(f"  Issues:          {stats['issues']}")
        print(f"  Overdue:         {stats['overdue']}")
        print("="*40)
    else:
        print(f"❌ Failed to get stats: {response.status_code}")
    
    print("\n" + "🎉"*15)
    print("   HOUSEKEEPING TESTS COMPLETED!")
    print("🎉"*15)

if __name__ == "__main__":
    # First, make sure we have rooms
    print("Checking server connection...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️ Server responded but health check failed")
    except:
        print("❌ Server is not running!")
        print("Please start the server first:")
        print("  uvicorn main:app --reload")
        exit()
    
    test_housekeeping_workflow()