# setup_hotel_and_rooms.py
import requests

BASE_URL = "http://localhost:8000/api/v1"

def setup():
    print("🏨 Setting up THEO with hotels and rooms...")
    print("="*50)
    
    # Login as manager
    print("Logging in as manager...")
    login = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "manager",
        "password": "Manager123!"
    })
    
    if login.status_code != 200:
        print("❌ Login failed! Make sure server is running and manager user exists.")
        print(f"Response: {login.text}")
        return
    
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Check if hotel exists
    print("\nChecking for existing hotels...")
    hotels_response = requests.get(f"{BASE_URL}/hotels/", headers=headers)
    hotels = hotels_response.json()
    
    if hotels:
        hotel_id = hotels[0]["id"]
        print(f"✅ Using existing hotel: {hotels[0]['name']} (ID: {hotel_id})")
    else:
        # Create hotel
        print("Creating new hotel...")
        hotel_data = {
            "name": "Grand Hotel",
            "address": "123 Main Street, City Center",
            "phone": "+1234567890",
            "email": "grand@hotel.com",
            "total_rooms": 0
        }
        response = requests.post(f"{BASE_URL}/hotels/", params=hotel_data, headers=headers)
        if response.status_code == 200:
            hotel_id = response.json()["hotel"]["id"]
            print(f"✅ Created hotel: Grand Hotel (ID: {hotel_id})")
        else:
            print(f"❌ Failed to create hotel: {response.json()}")
            return
    
    # Create rooms
    print("\nCreating rooms...")
    rooms_to_create = [
        {"room_number": "101", "floor": 1, "room_type": "standard", "price_per_night": 15000, "max_occupancy": 2, "has_view": False, "description": "Standard room"},
        {"room_number": "102", "floor": 1, "room_type": "standard", "price_per_night": 15000, "max_occupancy": 2, "has_view": True, "description": "Standard room with ocean view"},
        {"room_number": "201", "floor": 2, "room_type": "deluxe", "price_per_night": 25000, "max_occupancy": 4, "has_view": True, "description": "Deluxe suite with balcony"},
    ]
    
    created_count = 0
    for room_data in rooms_to_create:
        room_data["hotel_id"] = hotel_id
        response = requests.post(f"{BASE_URL}/rooms/", json=room_data, headers=headers)
        
        if response.status_code == 201:
            room = response.json()
            print(f"  ✅ Created Room {room_data['room_number']} (ID: {room['id']})")
            created_count += 1
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"  ⚠️ Room {room_data['room_number']} already exists")
        else:
            print(f"  ❌ Failed to create Room {room_data['room_number']}: {response.text}")
    
    # Show all rooms
    print("\n" + "="*50)
    print("📋 Current Rooms in System:")
    print("="*50)
    rooms_response = requests.get(f"{BASE_URL}/rooms/", headers=headers)
    if rooms_response.status_code == 200:
        rooms = rooms_response.json()
        for room in rooms:
            price = room['price_per_night'] / 100
            print(f"  Room {room['room_number']} | Floor {room['floor']} | {room['room_type']} | ${price:.2f}/night | Status: {room['status']}")
    
    print("\n" + "="*50)
    print(f"✅ Setup complete! Created {created_count} new rooms.")
    print("="*50)
    print("\nNow you can run: python test_housekeeping.py")

if __name__ == "__main__":
    setup()