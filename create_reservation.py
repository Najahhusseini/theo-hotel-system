import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# Login
login = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "frontdesk",
    "password": "Front123!"
})

if login.status_code != 200:
    print("Login failed")
    exit()

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get guests
guests_response = requests.get(f"{BASE_URL}/guests/", headers=headers)
guests = guests_response.json()

# Find Payment Test guest
guest_id = None
for g in guests:
    if g['email'] == 'payment@test.com':
        guest_id = g['id']
        print(f"Found guest: {g['first_name']} {g['last_name']} (ID: {guest_id})")

if not guest_id:
    print("Creating new guest...")
    new_guest = {
        "first_name": "Payment",
        "last_name": "Test",
        "email": "payment@test.com",
        "phone": "1234567890"
    }
    guest_response = requests.post(f"{BASE_URL}/guests/", json=new_guest, headers=headers)
    guest_id = guest_response.json()['id']
    print(f"Created guest with ID: {guest_id}")

# Get rooms
rooms_response = requests.get(f"{BASE_URL}/rooms/", headers=headers)
rooms = rooms_response.json()

# Find a clean room
room_id = None
for r in rooms:
    if r['status'] == 'clean':
        room_id = r['id']
        print(f"Using room: {r['room_number']} (ID: {room_id})")
        break

if not room_id:
    room_id = rooms[0]['id']
    print(f"Using room ID: {room_id}")

# Create reservation with check-in date today
check_in = datetime.now() - timedelta(hours=2)
check_out = check_in + timedelta(days=2)

reservation_data = {
    "guest_name": "Payment Test",
    "guest_email": "payment@test.com",
    "guest_phone": "1234567890",
    "check_in_date": check_in.isoformat(),
    "check_out_date": check_out.isoformat(),
    "number_of_guests": 2,
    "room_id": room_id,
    "hotel_id": 1,
    "guest_id": guest_id
}

print(f"\nCreating reservation...")
response = requests.post(f"{BASE_URL}/reservations/", json=reservation_data, headers=headers)

if response.status_code == 201:
    reservation = response.json()
    print(f"✅ Reservation created!")
    print(f"   ID: {reservation['id']}")
    print(f"   Number: {reservation['reservation_number']}")
    print(f"   Guest ID: {reservation['guest_id']}")
    print(f"   Room ID: {reservation['room_id']}")
    print(f"   Total: ${reservation['total_price']:.2f}")
else:
    print(f"❌ Failed: {response.json()}")