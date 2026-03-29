# test_guests.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_create_guest():
    """Test creating a guest profile"""
    print("\n" + "="*50)
    print("👤 CREATING GUEST PROFILE")
    print("="*50)
    
    guest_data = {
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@example.com",
        "phone": "+1234567890",
        "address": "123 Main St",
        "city": "New York",
        "country": "USA",
        "preferences": {
            "pillow_type": "feather",
            "floor_preference": "high",
            "extra_towels": True
        },
        "special_notes": "VIP guest, allergic to feathers",
        "marketing_consent": True
    }
    
    response = requests.post(f"{BASE_URL}/guests/", json=guest_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        guest = response.json()
        print(f"✅ Guest created successfully!")
        print(f"   Guest Code: {guest['guest_code']}")
        print(f"   Name: {guest['first_name']} {guest['last_name']}")
        print(f"   Email: {guest['email']}")
        print(f"   Loyalty Level: {guest['loyalty_level']}")
        return guest
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_search_guests():
    """Test searching for guests"""
    print("\n" + "="*50)
    print("🔍 SEARCHING GUESTS")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/guests/search", params={"q": "john"})
    if response.status_code == 200:
        results = response.json()
        if results:
            print(f"Found {len(results)} result(s):")
            for guest in results:
                print(f"  • {guest['full_name']} ({guest['guest_code']})")
                print(f"    {guest['email']} | {guest['phone']}")
                print(f"    Loyalty: {guest['loyalty_level']} | Stays: {guest['total_stays']}")
        else:
            print("No guests found")
    else:
        print(f"❌ Error: {response.status_code}")

def test_get_guest(guest_id):
    """Test getting a specific guest"""
    print("\n" + "="*50)
    print(f"👤 GUEST DETAILS (ID: {guest_id})")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/guests/{guest_id}")
    if response.status_code == 200:
        guest = response.json()
        print(f"Guest: {guest['first_name']} {guest['last_name']}")
        print(f"Code: {guest['guest_code']}")
        print(f"Email: {guest['email']}")
        print(f"Phone: {guest['phone']}")
        print(f"Loyalty: {guest['loyalty_level']} ({guest['loyalty_points']} points)")
        print(f"Total Stays: {guest['total_stays']}")
        print(f"Total Spent: ${guest['total_spent']:.2f}")
        if guest['preferences']:
            print(f"Preferences: {guest['preferences']}")
    else:
        print(f"❌ Error: {response.status_code}")

def test_update_guest(guest_id):
    """Test updating a guest"""
    print("\n" + "="*50)
    print("✏️ UPDATING GUEST")
    print("="*50)
    
    update_data = {
        "special_notes": "VIP guest, allergic to feathers, prefers high floor",
        "preferences": {
            "pillow_type": "feather",
            "floor_preference": "high",
            "extra_towels": True,
            "early_check_in": True
        }
    }
    
    response = requests.put(f"{BASE_URL}/guests/{guest_id}", json=update_data)
    if response.status_code == 200:
        guest = response.json()
        print(f"✅ Guest updated!")
        print(f"   Special Notes: {guest['special_notes']}")
        print(f"   Preferences: {guest['preferences']}")
    else:
        print(f"❌ Error: {response.status_code}")

def test_add_stay(guest_id):
    """Test adding a stay record"""
    print("\n" + "="*50)
    print("🏨 ADDING STAY RECORD")
    print("="*50)
    
    response = requests.post(
        f"{BASE_URL}/guests/{guest_id}/add-stay",
        params={"amount_spent": 450.00}
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
        print(f"   Guest: {result['guest']}")
        print(f"   Total Stays: {result['total_stays']}")
        print(f"   Total Spent: ${result['total_spent']:.2f}")
        print(f"   Loyalty Level: {result['loyalty_level']}")
    else:
        print(f"❌ Error: {response.status_code}")

def test_get_all_guests():
    """Test getting all guests"""
    print("\n" + "="*50)
    print("📋 ALL GUESTS")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/guests/")
    if response.status_code == 200:
        guests = response.json()
        if guests:
            print(f"Found {len(guests)} guest(s):")
            for guest in guests:
                print(f"  • {guest['first_name']} {guest['last_name']} ({guest['guest_code']})")
                print(f"    Loyalty: {guest['loyalty_level']} | Stays: {guest['total_stays']} | Spent: ${guest['total_spent']:.2f}")
        else:
            print("No guests found")
    else:
        print(f"❌ Error: {response.status_code}")

def run_all_tests():
    """Run all guest tests"""
    print("\n" + "👥"*15)
    print("   THEO GUEST CRM TEST SUITE")
    print("👥"*15)
    
    # Check server
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("⚠️ Server responded but health check failed")
    except:
        print("\n❌ ERROR: Server is not running!")
        print("Please start the server first:")
        print("  cd C:\\Users\\Najah\\THEO_v1\\backend")
        print("  venv\\Scripts\\activate")
        print("  uvicorn main:app --reload")
        return
    
    # Create guest
    guest = test_create_guest()
    
    if guest:
        # Get all guests
        test_get_all_guests()
        
        # Search guests
        test_search_guests()
        
        # Get guest details
        test_get_guest(guest['id'])
        
        # Update guest
        test_update_guest(guest['id'])
        
        # Add a stay record
        test_add_stay(guest['id'])
        
        # Get updated guest details
        print("\n" + "="*50)
        print("📊 UPDATED GUEST STATS")
        print("="*50)
        response = requests.get(f"{BASE_URL}/guests/{guest['id']}")
        if response.status_code == 200:
            updated_guest = response.json()
            print(f"Total Stays: {updated_guest['total_stays']}")
            print(f"Total Spent: ${updated_guest['total_spent']:.2f}")
            print(f"Loyalty Level: {updated_guest['loyalty_level']}")
        
        print("\n" + "🎉"*15)
        print("   GUEST CRM TESTS COMPLETED!")
        print("🎉"*15)
    else:
        print("\n❌ Could not create test guest")
        print("\nℹ️ If guest already exists, try running with a different email:")
        print("   Change 'john.smith@example.com' to something else in test_create_guest()")

if __name__ == "__main__":
    run_all_tests()