# create_test_users.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import get_password_hash

def create_test_users():
    """Create test users for each role"""
    db = SessionLocal()
    
    users = [
        {
            "username": "manager",
            "email": "manager@theo.com",
            "password": "Manager123!",
            "first_name": "Hotel",
            "last_name": "Manager",
            "role": UserRole.HOTEL_MANAGER
        },
        {
            "username": "frontdesk",
            "email": "frontdesk@theo.com",
            "password": "Front123!",
            "first_name": "Front",
            "last_name": "Desk",
            "role": UserRole.FRONT_DESK
        },
        {
            "username": "housekeeping",
            "email": "housekeeping@theo.com",
            "password": "House123!",
            "first_name": "House",
            "last_name": "Keeping",
            "role": UserRole.HOUSEKEEPING
        },
        {
            "username": "maintenance",
            "email": "maintenance@theo.com",
            "password": "Maint123!",
            "first_name": "Main",
            "last_name": "Tenance",
            "role": UserRole.MAINTENANCE
        },
        {
            "username": "accounting",
            "email": "accounting@theo.com",
            "password": "Acct123!",
            "first_name": "Account",
            "last_name": "Ant",
            "role": UserRole.ACCOUNTING
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for user_data in users:
        # Check if user already exists
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            print(f"⚠️ User {user_data['username']} already exists, skipping...")
            skipped_count += 1
            continue
        
        # Create user
        try:
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                is_active=True,
                is_locked=False,
                failed_login_attempts=0
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print(f"✅ Created: {user_data['username']} ({user_data['role'].value})")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Error creating {user_data['username']}: {e}")
            db.rollback()
    
    print("\n" + "="*50)
    print(f"📊 User Creation Summary:")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print("="*50)
    
    if created_count > 0:
        print("\n🔐 Test User Credentials:")
        print("-" * 40)
        for user_data in users:
            print(f"   {user_data['username']} / {user_data['password']}")
        print("-" * 40)
        print("   All passwords: The username + '123!' (e.g., Manager123!)")
    
    db.close()

if __name__ == "__main__":
    print("👥 Creating THEO Test Users")
    print("="*50)
    create_test_users()