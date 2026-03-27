import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login as admin
login = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "Admin123!"
})

if login.status_code != 200:
    print("Login failed")
    exit()

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check existing rooms
rooms = requests.get(f"{BASE_URL}/rooms/", headers=headers).json()
print(f"Found {len(rooms)} rooms")

if len(rooms) == 0:
    # Create a room
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
    print(f"Created room: {resp.status_code}")
    if resp.status_code == 201:
        print(f"Room created: {resp.json()['room_number']}")
else:
    print("Room already exists")