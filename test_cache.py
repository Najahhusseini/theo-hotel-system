import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("Logging in...")
login = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "Admin123!"
})

if login.status_code != 200:
    print("Login failed!")
    exit()

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful!")

# Create a room
print("\nCreating room...")
room = {
    "room_number": "101",
    "floor": 1,
    "room_type": "standard",
    "price_per_night": 15000,
    "max_occupancy": 2,
    "has_view": False,
    "description": "Standard room",
    "hotel_id": 1
}
resp = requests.post(f"{BASE_URL}/rooms/", json=room, headers=headers)
if resp.status_code == 201:
    room_data = resp.json()
    room_id = room_data["id"]
    print(f"Room created! ID: {room_id}")
    
    # Set room status to clean
    print("\nSetting room status to clean...")
    status_resp = requests.put(f"{BASE_URL}/rooms/{room_id}/status", params={"status": "clean"}, headers=headers)
    print(f"Status update: {status_resp.status_code}")
else:
    print(f"Room creation failed: {resp.text}")
    # Try to get existing rooms
    rooms = requests.get(f"{BASE_URL}/rooms/", headers=headers).json()
    if rooms:
        room_id = rooms[0]["id"]
        print(f"Using existing room ID: {room_id}")
    else:
        exit()

# Test available rooms - first request
print("\n=== First request (should be cache miss) ===")
resp1 = requests.get(f"{BASE_URL}/rooms/available?hotel_id=1", headers=headers)
print(f"Status: {resp1.status_code}")
print(f"Rooms found: {len(resp1.json()) if resp1.status_code == 200 else 0}")

# Test available rooms - second request (should hit cache)
print("\n=== Second request (should hit cache) ===")
resp2 = requests.get(f"{BASE_URL}/rooms/available?hotel_id=1", headers=headers)
print(f"Status: {resp2.status_code}")
print(f"Rooms found: {len(resp2.json()) if resp2.status_code == 200 else 0}")

# Check cache stats
print("\n=== Cache Statistics ===")
stats = requests.get(f"{BASE_URL}/monitoring/cache-stats", headers=headers)
if stats.status_code == 200:
    print(stats.json())
else:
    print(f"Failed to get cache stats: {stats.status_code}")

print("\n✅ Done!")