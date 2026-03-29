# test_billing.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login(username, password):
    """Login helper"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_billing_workflow():
    """Test complete billing workflow"""
    print("\n" + "💰"*15)
    print("   THEO BILLING SYSTEM TEST")
    print("💰"*15)
    
    # Login as front desk
    token = login("frontdesk", "Front123!")
    if not token:
        print("❌ Front desk login failed!")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Front desk logged in")
    
    # First, check if we have a reservation
    print("\n📋 Checking for existing reservations...")
    response = requests.get(f"{BASE_URL}/reservations/", headers=headers)
    
    if response.status_code == 200:
        reservations = response.json()
        if not reservations:
            print("❌ No reservations found!")
            print("   Please create a reservation first using test_reservations.py")
            return
        reservation = reservations[0]
        print(f"✅ Found reservation: {reservation['reservation_number']}")
        reservation_id = reservation['id']
        guest_id = reservation.get('guest_id')
        hotel_id = reservation['hotel_id']
    else:
        print("❌ Could not get reservations")
        return
    
    # Create folio
    print("\n💰 Creating folio...")
    folio_data = {
        "reservation_id": reservation_id,
        "guest_id": guest_id if guest_id else 1,
        "hotel_id": hotel_id
    }
    
    response = requests.post(f"{BASE_URL}/billing/folios", json=folio_data, headers=headers)
    
    if response.status_code == 201:
        folio = response.json()
        print(f"✅ Folio created: {folio['folio_number']} (ID: {folio['id']})")
        folio_id = folio['id']
    elif response.status_code == 400 and "already exists" in response.text:
        print("⚠️ Folio already exists, getting existing...")
        folio_response = requests.get(f"{BASE_URL}/billing/folios/reservation/{reservation_id}", headers=headers)
        folio = folio_response.json()
        folio_id = folio['id']
        print(f"✅ Using existing folio: {folio['folio_number']}")
    else:
        print(f"❌ Failed: {response.json()}")
        return
    
    # Add room charge
    print("\n🏨 Adding room charge...")
    charge_data = {
        "transaction_type": "room_charge",
        "description": "Room rate - 2 nights",
        "amount": 300.00,
        "tax": 30.00
    }
    
    response = requests.post(f"{BASE_URL}/billing/folios/{folio_id}/charges", json=charge_data, headers=headers)
    
    if response.status_code == 200:
        transaction = response.json()
        print(f"✅ Charge added: {transaction['description']} - ${transaction['amount']:.2f}")
    else:
        print(f"❌ Failed: {response.json()}")
    
    # Add restaurant charge
    print("\n🍽️ Adding restaurant charge...")
    charge_data = {
        "transaction_type": "food_beverage",
        "description": "Restaurant - Dinner for 2",
        "amount": 85.50,
        "tax": 8.55
    }
    
    response = requests.post(f"{BASE_URL}/billing/folios/{folio_id}/charges", json=charge_data, headers=headers)
    
    if response.status_code == 200:
        transaction = response.json()
        print(f"✅ Charge added: {transaction['description']} - ${transaction['amount']:.2f}")
    else:
        print(f"❌ Failed: {response.json()}")
    
    # Get folio summary
    print("\n📊 Getting folio summary...")
    response = requests.get(f"{BASE_URL}/billing/folios/{folio_id}/summary", headers=headers)
    
    if response.status_code == 200:
        summary = response.json()
        print("\n💰 FOLIO SUMMARY:")
        print("="*40)
        print(f"  Folio: {summary['folio_number']}")
        print(f"  Guest: {summary['guest_name']}")
        print(f"  Room: {summary['room_number']}")
        print(f"  Subtotal: ${summary['subtotal']:.2f}")
        print(f"  Tax: ${summary['tax']:.2f}")
        print(f"  Total: ${summary['total']:.2f}")
        print(f"  Paid: ${summary['paid']:.2f}")
        print(f"  Balance: ${summary['balance']:.2f}")
        print("="*40)
    else:
        print(f"❌ Failed: {response.json()}")
    
    # Add payment
    print("\n💳 Processing payment...")
    payment_data = {
        "amount": summary['balance'],
        "payment_method": "credit_card",
        "payment_reference": "VISA-1234",
        "notes": "Payment for stay"
    }
    
    response = requests.post(f"{BASE_URL}/billing/folios/{folio_id}/payments", json=payment_data, headers=headers)
    
    if response.status_code == 200:
        payment = response.json()
        print(f"✅ Payment processed: ${payment['amount']:.2f}")
        print(f"   New balance: ${payment['new_balance']:.2f}")
    else:
        print(f"❌ Failed: {response.json()}")
    
    # Close folio
    print("\n🔒 Closing folio...")
    response = requests.post(f"{BASE_URL}/billing/folios/{folio_id}/close", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
        print(f"   Total paid: ${result['total_paid']:.2f}")
    else:
        print(f"❌ Failed: {response.json()}")
    
    print("\n" + "🎉"*15)
    print("   BILLING SYSTEM TESTS COMPLETED!")
    print("🎉"*15)

if __name__ == "__main__":
    test_billing_workflow()