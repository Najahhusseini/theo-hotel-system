# test_maintenance.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login(username, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_maintenance_workflow():
    print("\n" + "🔧"*15)
    print("   THEO MAINTENANCE MODULE TEST")
    print("🔧"*15)
    
    # Login as front desk to report issue
    front_token = login("frontdesk", "Front123!")
    if not front_token:
        print("❌ Front desk login failed!")
        return
    print("✅ Front desk logged in")
    
    # Create maintenance request
    print("\n📝 Creating maintenance request...")
    headers = {"Authorization": f"Bearer {front_token}"}
    request_data = {
        "category": "plumbing",
        "priority": "high",
        "title": "Leaking faucet in room 101",
        "description": "Water is leaking from bathroom faucet, guest complaining",
        "room_id": 1,
        "hotel_id": 1,
        "reported_by_name": "Front Desk Staff"
    }
    
    response = requests.post(f"{BASE_URL}/maintenance/requests", json=request_data, headers=headers)
    
    if response.status_code == 201:
        request = response.json()
        print(f"✅ Request created: {request['request_number']}")
        request_id = request['id']
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Login as manager to assign
    manager_token = login("manager", "Manager123!")
    if not manager_token:
        print("❌ Manager login failed!")
        return
    print("✅ Manager logged in")
    
    # Get maintenance staff ID
    headers = {"Authorization": f"Bearer {manager_token}"}
    users_response = requests.get(f"{BASE_URL}/auth/users/", headers=headers)
    maintenance_id = None
    
    if users_response.status_code == 200:
        for user in users_response.json():
            if user['role'] == 'maintenance':
                maintenance_id = user['id']
                print(f"Found maintenance staff: {user['username']} (ID: {maintenance_id})")
                break
    
    if not maintenance_id:
        print("❌ Could not find maintenance staff")
        return
    
    # Assign request
    print("\n👥 Assigning request to maintenance...")
    headers = {"Authorization": f"Bearer {manager_token}"}
    assign_data = {"assigned_to_id": maintenance_id}
    response = requests.put(f"{BASE_URL}/maintenance/requests/{request_id}/assign", json=assign_data, headers=headers)
    
    if response.status_code == 200:
        print("✅ Request assigned")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Login as maintenance staff
    maint_token = login("maintenance", "Maint123!")
    if not maint_token:
        print("❌ Maintenance login failed!")
        return
    print("✅ Maintenance staff logged in")
    
    # Start work
    print("\n🔨 Starting work...")
    headers = {"Authorization": f"Bearer {maint_token}"}
    response = requests.put(f"{BASE_URL}/maintenance/requests/{request_id}/start", headers=headers)
    
    if response.status_code == 200:
        print("✅ Work started")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Complete work
    print("\n✅ Completing work...")
    complete_data = {
        "resolution_notes": "Replaced faucet washer, no more leak",
        "parts_used": "Faucet washer, plumber's tape",
        "cost": 25.50
    }
    response = requests.put(f"{BASE_URL}/maintenance/requests/{request_id}/complete", json=complete_data, headers=headers)
    
    if response.status_code == 200:
        print("✅ Work completed")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Verify completion
    print("\n✓ Verifying completion...")
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = requests.put(f"{BASE_URL}/maintenance/requests/{request_id}/verify", headers=headers)
    
    if response.status_code == 200:
        print("✅ Request verified")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Get dashboard stats
    print("\n📊 Getting maintenance stats...")
    response = requests.get(f"{BASE_URL}/maintenance/stats", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print("\n🔧 Maintenance Dashboard:")
        print("="*40)
        print(f"  Total Requests:  {stats['total_requests']}")
        print(f"  Reported:        {stats['reported']}")
        print(f"  Assigned:        {stats['assigned']}")
        print(f"  In Progress:     {stats['in_progress']}")
        print(f"  Completed:       {stats['completed']}")
        print(f"  Verified:        {stats['verified']}")
        print(f"  Cancelled:       {stats['cancelled']}")
        print(f"  Overdue:         {stats['overdue']}")
        print(f"  Avg Time:        {stats['avg_completion_time_hours']} hours")
        print("="*40)
    
    print("\n" + "🎉"*15)
    print("   MAINTENANCE TESTS COMPLETED!")
    print("🎉"*15)

if __name__ == "__main__":
    # Check if server is running
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
    
    test_maintenance_workflow()
    test_maintenance_workflow()