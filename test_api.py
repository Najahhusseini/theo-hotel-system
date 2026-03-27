# test_api.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_test_hotel():
    """Create a test hotel, or get existing one"""
    print("\n" + "="*50)
    print("📋 CREATING/GETTING TEST HOTEL")
    print("="*50)
    
    hotel_data = {
        "name": "Grand Hotel",
        "address": "123 Main Street, City Center",
        "phone": "+1234567890",
        "email": "grand@hotel.com",
        "total_rooms": 0
    }
    
    # Try to create a new hotel
    response = requests.post(f"{BASE_URL}/hotels/", params=hotel_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        hotel = response.json()
        print(f"✅ New hotel created successfully!")
        print(f"   ID: {hotel['hotel']['id']}")
        print(f"   Name: {hotel['hotel']['name']}")
        return hotel['hotel']['id']
    elif response.status_code == 400:
        # Hotel already exists, let's get it from the list
        print(f"ℹ️  Hotel already exists, fetching from database...")
        
        # Get all hotels and find the one with our email
        response = requests.get(f"{BASE_URL}/hotels/")
        if response.status_code == 200:
            hotels = response.json()
            for hotel in hotels:
                if hotel['email'] == "grand@hotel.com":
                    print(f"✅ Found existing hotel!")
                    print(f"   ID: {hotel['id']}")
                    print(f"   Name: {hotel['name']}")
                    return hotel['id']
        
        print(f"❌ Could not find hotel with email grand@hotel.com")
        return None
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_create_rooms(hotel_id):
    """Test creating multiple rooms"""
    print("\n" + "="*50)
    print("🏨 CREATING ROOMS")
    print("="*50)
    
    rooms = [
        {
            "room_number": "101",
            "floor": 1,
            "room_type": "standard",
            "price_per_night": 15000,
            "max_occupancy": 2,
            "has_view": False,
            "description": "Standard room with city view",
            "hotel_id": hotel_id
        },
        {
            "room_number": "102",
            "floor": 1,
            "room_type": "standard",
            "price_per_night": 15000,
            "max_occupancy": 2,
            "has_view": True,
            "description": "Standard room with ocean view",
            "hotel_id": hotel_id
        },
        {
            "room_number": "201",
            "floor": 2,
            "room_type": "deluxe",
            "price_per_night": 25000,
            "max_occupancy": 4,
            "has_view": True,
            "description": "Deluxe suite with balcony",
            "hotel_id": hotel_id
        }
    ]
    
    created_count = 0
    for room in rooms:
        response = requests.post(f"{BASE_URL}/rooms/", json=room)
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Created Room {room['room_number']} (ID: {data['id']})")
            created_count += 1
        elif response.status_code == 400:
            print(f"ℹ️  Room {room['room_number']} already exists, skipping...")
        else:
            print(f"❌ Failed to create Room {room['room_number']}: {response.json()}")
    
    if created_count == 0:
        print("No new rooms were created (they may already exist)")
    else:
        print(f"Created {created_count} new room(s)")

def test_get_all_rooms():
    """Test getting all rooms"""
    print("\n" + "="*50)
    print("📋 ALL ROOMS")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/rooms/")
    if response.status_code == 200:
        rooms = response.json()
        if rooms:
            print(f"Found {len(rooms)} rooms:")
            for room in rooms:
                price = room['price_per_night'] / 100
                print(f"  • Room {room['room_number']} (Floor {room['floor']})")
                print(f"    Type: {room['room_type']} | Price: ${price:.2f}/night")
                print(f"    Status: {room['status']} | Max: {room['max_occupancy']} guests")
                print()
        else:
            print("No rooms found in the system")
    else:
        print(f"❌ Error: {response.status_code}")

def test_get_room_by_id(room_id):
    """Test getting a specific room"""
    print("\n" + "="*50)
    print(f"🔍 ROOM ID {room_id}")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/rooms/{room_id}")
    if response.status_code == 200:
        room = response.json()
        price = room['price_per_night'] / 100
        print(f"Room {room['room_number']} Details:")
        print(f"  • Type: {room['room_type']}")
        print(f"  • Price: ${price:.2f}/night")
        print(f"  • Status: {room['status']}")
        print(f"  • Max Occupancy: {room['max_occupancy']}")
        print(f"  • Has View: {'Yes' if room['has_view'] else 'No'}")
        if room['description']:
            print(f"  • Description: {room['description']}")
    else:
        print(f"❌ Room not found or error: {response.status_code}")

def test_update_room_status(room_id):
    """Test updating room status"""
    print("\n" + "="*50)
    print("🔄 UPDATING ROOM STATUS")
    print("="*50)
    
    # First, get current status
    response = requests.get(f"{BASE_URL}/rooms/{room_id}")
    if response.status_code == 200:
        room = response.json()
        print(f"Current status of Room {room['room_number']}: {room['status']}")
    
    # Change to occupied
    print("\n1. Changing to OCCUPIED...")
    response = requests.put(
        f"{BASE_URL}/rooms/{room_id}/status",
        params={"status": "occupied"}
    )
    if response.status_code == 200:
        room = response.json()
        print(f"   ✅ Room {room['room_number']} status: {room['status']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Change to dirty (housekeeping will do this after check-out)
    print("\n2. Changing to DIRTY...")
    response = requests.put(
        f"{BASE_URL}/rooms/{room_id}/status",
        params={"status": "dirty"}
    )
    if response.status_code == 200:
        room = response.json()
        print(f"   ✅ Room {room['room_number']} status: {room['status']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Change to clean (housekeeping will do this after cleaning)
    print("\n3. Changing to CLEAN...")
    response = requests.put(
        f"{BASE_URL}/rooms/{room_id}/status",
        params={"status": "clean"}
    )
    if response.status_code == 200:
        room = response.json()
        print(f"   ✅ Room {room['room_number']} status: {room['status']}")
    else:
        print(f"   ❌ Error: {response.status_code}")

def test_available_rooms(hotel_id):
    """Test getting available rooms"""
    print("\n" + "="*50)
    print("✅ AVAILABLE ROOMS")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/rooms/available", params={"hotel_id": hotel_id})
    if response.status_code == 200:
        rooms = response.json()
        if rooms:
            print(f"Found {len(rooms)} available rooms:")
            for room in rooms:
                price = room['price_per_night'] / 100
                print(f"  • Room {room['room_number']}: ${price:.2f}/night")
        else:
            print("No available rooms at the moment")
    else:
        print(f"❌ Error: {response.status_code}")

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "🚀"*15)
    print("   THEO API TEST SUITE")
    print("🚀"*15)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("⚠️  Server responded but health check failed")
    except:
        print("\n❌ ERROR: Server is not running!")
        print("Please start the server first:")
        print("  cd C:\\Users\\Najah\\THEO_v1\\backend")
        print("  venv\\Scripts\\activate")
        print("  uvicorn main:app --reload")
        return
    
    # Create or get hotel
    hotel_id = create_test_hotel()
    
    if hotel_id:
        # Create rooms
        test_create_rooms(hotel_id)
        
        # Get all rooms
        test_get_all_rooms()
        
        # Get specific room (assuming room ID 1 exists)
        test_get_room_by_id(1)
        
        # Update room status
        test_update_room_status(1)
        
        # Get available rooms
        test_available_rooms(hotel_id)
        
        print("\n" + "🎉"*15)
        print("   ALL TESTS COMPLETED!")
        print("🎉"*15)
    else:
        print("\n❌ Failed to get/create test hotel.")

if __name__ == "__main__":
    run_all_tests()