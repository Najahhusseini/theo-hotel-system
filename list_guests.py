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

# Get guests
response = requests.get(f"{BASE_URL}/guests/", headers=headers)
guests = response.json()

print("\n📋 Guests:")
print("="*50)
for g in guests:
    print(f"ID: {g['id']}, Name: {g['first_name']} {g['last_name']}, Email: {g['email']}")