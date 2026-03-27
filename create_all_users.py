# create_all_users.py
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def login(username, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def create_user(token, username, password, email, first_name, last_name, role, hotel_id=None):
    headers = {"Authorization": f"Bearer {token}"}
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "role": role
    }
    if hotel_id:
        user_data["hotel_id"] = hotel_id
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data, headers=headers)
    if response.status_code == 201:
        print(f"✅ Created {role}: {username}")
        return response.json()
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"⚠️ {username} already exists")
        return None
    else:
        print(f"❌ Failed to create {username}: {response.json()}")
        return None

def main():
    print("\n👥 Creating THEO Test Users")
    print("="*50)
    
    # Login as admin first
    admin_token = login("admin", "Admin123!")
    if not admin_token:
        print("❌ Admin login failed! Please create admin first:")
        print("   python create_admin.py")
        return
    
    print("✅ Admin logged in")
    
    # Create all users
    users = [
        ("manager", "Manager123!", "manager@theo.com", "Hotel", "Manager", "hotel_manager"),
        ("frontdesk", "Front123!", "frontdesk@theo.com", "Front", "Desk", "front_desk"),
        ("housekeeping", "House123!", "housekeeping@theo.com", "House", "Keeping", "housekeeping"),
        ("maintenance", "Maint123!", "maintenance@theo.com", "Main", "Tenance", "maintenance"),
        ("accounting", "Acct123!", "accounting@theo.com", "Account", "Ant", "accounting"),
        ("maintstaff", "Maint123!", "maintstaff@theo.com", "Main", "Staff", "maintenance")
    ]
    
    for username, password, email, first, last, role in users:
        create_user(admin_token, username, password, email, first, last, role)
    
    print("\n" + "="*50)
    print("🔐 Test User Credentials:")
    print("-"*40)
    for username, password, email, first, last, role in users:
        print(f"   {username} / {password} ({role})")
    print("-"*40)
    print("\n✅ All users created successfully!")

if __name__ == "__main__":
    main()