import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

print("Logging in...")
login = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "Admin123!"
})

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful!")

print("\n=== Running 5 requests to test caching ===")
for i in range(5):
    start = time.time()
    response = requests.get(f"{BASE_URL}/rooms/available?hotel_id=1", headers=headers)
    elapsed = (time.time() - start) * 1000
    print(f"Request {i+1}: Status={response.status_code}, Rooms={len(response.json())}, Time={elapsed:.2f}ms")

print("\n=== Cache Statistics ===")
stats = requests.get(f"{BASE_URL}/monitoring/cache-stats", headers=headers)
print(stats.json())