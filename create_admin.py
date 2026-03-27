# create_admin.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import get_password_hash

def create_admin_user():
    db = SessionLocal()
    
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists!")
            return
        
        password = "Admin123!"
        hashed_password = get_password_hash(password)
        
        admin = User(
            username="admin",
            email="admin@theo.com",
            password_hash=hashed_password,
            first_name="System",
            last_name="Administrator",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("="*50)
        print("✅ Super Admin created successfully!")
        print("="*50)
        print(f"Username: admin")
        print(f"Email: admin@theo.com")
        print(f"Password: Admin123!")
        print("="*50)
        
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()