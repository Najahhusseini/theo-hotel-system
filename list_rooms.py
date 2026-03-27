import requests

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

# Get rooms
response = requests.get(f"{BASE_URL}/rooms/", headers=headers)
rooms = response.json()

print("\n🏨 Rooms:")
print("="*50)
for r in rooms:
    print(f"ID: {r['id']}, Number: {r['room_number']}, Status: {r['status']}")