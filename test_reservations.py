# test_reservations.py
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_create_reservation():
    """Test creating a reservation"""
    print("\n" + "="*50)
    print("📝 CREATING RESERVATION")
    print("="*50)
    
    # Set dates for booking (tomorrow for 3 nights)
    check_in = datetime.now() + timedelta(days=1)
    check_out = check_in + timedelta(days=3)
    
    reservation_data = {
        "guest_name": "John Smith",
        "guest_email": "john.smith@example.com",
        "guest_phone": "+1234567890",
        "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat(),
        "number_of_guests": 2,
        "special_requests": "Extra pillows and a quiet room",
        "room_id": 1,  # Room 101
        "hotel_id": 1   # Grand Hotel
    }
    
    response = requests.post(f"{BASE_URL}/reservations/", json=reservation_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        reservation = response.json()
        print(f"✅ Reservation created successfully!")
        print(f"   Reservation Number: {reservation['reservation_number']}")
        print(f"   Guest: {reservation['guest_name']}")
        print(f"   Room: {reservation['room_id']}")
        print(f"   Dates: {reservation['check_in_date']} to {reservation['check_out_date']}")
        print(f"   Total Price: ${reservation['total_price']:.2f}")
        return reservation
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_get_reservations():
    """Test getting all reservations"""
    print("\n" + "="*50)
    print("📋 ALL RESERVATIONS")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/reservations/")
    if response.status_code == 200:
        reservations = response.json()
        if reservations:
            print(f"Found {len(reservations)} reservation(s):")
            for res in reservations:
                print(f"  • {res['reservation_number']} - {res['guest_name']}")
                print(f"    Room: {res['room_id']} | ${res['total_price']:.2f}")
                print(f"    Status: {res['status']}")
                print(f"    Dates: {res['check_in_date'][:10]} to {res['check_out_date'][:10]}")
                print()
        else:
            print("No reservations found")
    else:
        print(f"❌ Error: {response.status_code}")

def test_get_today_arrivals():
    """Test getting today's arrivals"""
    print("\n" + "="*50)
    print("🚪 TODAY'S ARRIVALS")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/reservations/today/arrivals")
    if response.status_code == 200:
        arrivals = response.json()
        if arrivals:
            print(f"Found {len(arrivals)} arrival(s) today:")
            for arr in arrivals:
                print(f"  • {arr['guest_name']} - Room {arr['room_id']}")
                print(f"    Reservation: {arr['reservation_number']}")
        else:
            print("No arrivals today")
    else:
        print(f"❌ Error: {response.status_code}")

def test_update_reservation(reservation_id):
    """Test updating a reservation"""
    print("\n" + "="*50)
    print("✏️ UPDATING RESERVATION")
    print("="*50)
    
    update_data = {
        "special_requests": "Extra pillows, ocean view, and late check-out"
    }
    
    response = requests.put(f"{BASE_URL}/reservations/{reservation_id}", json=update_data)
    if response.status_code == 200:
        reservation = response.json()
        print(f"✅ Reservation updated!")
        print(f"   Special Requests: {reservation['special_requests']}")
    else:
        print(f"❌ Error: {response.status_code}")

def test_check_in(reservation_id):
    """Test checking in"""
    print("\n" + "="*50)
    print("🏨 CHECKING IN")
    print("="*50)
    
    response = requests.post(f"{BASE_URL}/reservations/{reservation_id}/check-in")
    if response.status_code == 200:
        reservation = response.json()
        print(f"✅ Checked in successfully!")
        print(f"   Guest: {reservation['guest_name']}")
        print(f"   Status: {reservation['status']}")
        
        # Check room status
        room_response = requests.get(f"{BASE_URL}/rooms/{reservation['room_id']}")
        if room_response.status_code == 200:
            room = room_response.json()
            print(f"   Room {room['room_number']} status: {room['status']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.json()}")

def test_check_out(reservation_id):
    """Test checking out"""
    print("\n" + "="*50)
    print("🧹 CHECKING OUT")
    print("="*50)
    
    response = requests.post(f"{BASE_URL}/reservations/{reservation_id}/check-out")
    if response.status_code == 200:
        reservation = response.json()
        print(f"✅ Checked out successfully!")
        print(f"   Guest: {reservation['guest_name']}")
        print(f"   Status: {reservation['status']}")
        
        # Check room status
        room_response = requests.get(f"{BASE_URL}/rooms/{reservation['room_id']}")
        if room_response.status_code == 200:
            room = room_response.json()
            print(f"   Room {room['room_number']} status: {room['status']} (needs cleaning)")
    else:
        print(f"❌ Error: {response.status_code}")

def run_all_tests():
    """Run all reservation tests"""
    print("\n" + "🏨"*15)
    print("   THEO RESERVATION TEST SUITE")
    print("🏨"*15)
    
    # Check server
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print("✅ Server is running!")
    except:
        print("\n❌ Server is not running!")
        return
    
    # Create a reservation
    reservation = test_create_reservation()
    
    if reservation:
        # Get all reservations
        test_get_reservations()
        
        # Get today's arrivals
        test_get_today_arrivals()
        
        # Update reservation
        test_update_reservation(reservation['id'])
        
        # Check in
        test_check_in(reservation['id'])
        
        # Check out
        test_check_out(reservation['id'])
        
        print("\n" + "🎉"*15)
        print("   RESERVATION TESTS COMPLETED!")
        print("🎉"*15)
    else:
        print("\n❌ Could not create test reservation")

if __name__ == "__main__":
    run_all_tests()