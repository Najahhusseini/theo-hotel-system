from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.models.user import User
from app.models.hotel import Hotel
from app.models.room import Room
from app.utils.security import get_password_hash
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/one-time-setup", tags=["setup"])
logger = logging.getLogger(__name__)

@router.get("/fix-admin")
def fix_admin(db: Session = Depends(get_db)):
    """One-time endpoint to fix admin account"""
    try:
        results = []
        
        # Find admin user
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            # Force unlock admin
            admin.is_active = True
            # Reset any lock fields
            if hasattr(admin, 'failed_login_attempts'):
                admin.failed_login_attempts = 0
            if hasattr(admin, 'locked_until'):
                admin.locked_until = None
            
            # Update password to ensure it's correct
            admin.hashed_password = get_password_hash("admin123")
            
            results.append(f"✅ Updated existing admin: {admin.username}")
        else:
            # Create new admin
            admin = User(
                username="admin",
                email="admin@theo.com",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            results.append("✅ Created new admin user")
        
        # Create a test hotel if none exists
        hotel = db.query(Hotel).first()
        if not hotel:
            hotel = Hotel(
                name="Grand Hotel Downtown",
                address="123 Main St, City Center",
                phone="+1234567890",
                email="info@grandhotel.com",
                total_rooms=100,
                is_active=True
            )
            db.add(hotel)
            db.flush()
            results.append(f"✅ Created test hotel: {hotel.name}")
            
            # Create some test rooms
            room_types = ["standard", "deluxe", "suite"]
            for i in range(1, 6):
                room = Room(
                    room_number=f"{100 + i}",
                    room_type=room_types[i % 3],
                    floor=(i % 3) + 1,
                    price_per_night=100 + (i * 20),
                    status="available",
                    capacity=2,
                    hotel_id=hotel.id
                )
                db.add(room)
            results.append("✅ Created 5 test rooms")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Admin fixed and test data created",
            "details": results,
            "login": {
                "username": "admin",
                "password": "admin123"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in fix-admin: {e}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }