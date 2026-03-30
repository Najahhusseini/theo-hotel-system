from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.models.user import User
from app.models.hotel import Hotel
from app.models.room import Room, RoomType, RoomStatus
from app.utils.security import get_password_hash
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/one-time-setup", tags=["setup"])
logger = logging.getLogger(__name__)

@router.get("/fix-admin")
def fix_admin(db: Session = Depends(get_db)):
    """One-time endpoint to fix admin account and create test data"""
    try:
        results = []
        
        # Fix or create admin user
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
            db.flush()
            results.append("✅ Created new admin user")
        
        # Create test hotel if none exists
        hotel = db.query(Hotel).first()
        if not hotel:
            hotel = Hotel(
                name="Grand Hotel Downtown",
                address="123 Main St, City Center",
                phone="+1234567890",
                email="info@grandhotel.com",
                total_rooms=100
            )
            db.add(hotel)
            db.flush()
            results.append(f"✅ Created test hotel: {hotel.name}")
            
            # Create test rooms
            rooms_created = 0
            room_data = [
                {"room_number": "101", "floor": 1, "room_type": RoomType.STANDARD, "price_per_night": 15000, "max_occupancy": 2, "has_view": False},
                {"room_number": "102", "floor": 1, "room_type": RoomType.STANDARD, "price_per_night": 15000, "max_occupancy": 2, "has_view": False},
                {"room_number": "201", "floor": 2, "room_type": RoomType.DELUXE, "price_per_night": 25000, "max_occupancy": 2, "has_view": True},
                {"room_number": "202", "floor": 2, "room_type": RoomType.DELUXE, "price_per_night": 25000, "max_occupancy": 2, "has_view": True},
                {"room_number": "301", "floor": 3, "room_type": RoomType.SUITE, "price_per_night": 40000, "max_occupancy": 4, "has_view": True},
                {"room_number": "302", "floor": 3, "room_type": RoomType.PRESIDENTIAL, "price_per_night": 80000, "max_occupancy": 6, "has_view": True}
            ]
            
            for room_info in room_data:
                room = Room(
                    room_number=room_info["room_number"],
                    floor=room_info["floor"],
                    room_type=room_info["room_type"],
                    price_per_night=room_info["price_per_night"],
                    max_occupancy=room_info["max_occupancy"],
                    has_view=room_info["has_view"],
                    status=RoomStatus.CLEAN,
                    hotel_id=hotel.id
                )
                db.add(room)
                rooms_created += 1
            
            db.flush()
            results.append(f"✅ Created {rooms_created} test rooms")
        
        db.commit()
        
        # Test login to verify it works
        test_login = db.query(User).filter(User.username == "admin", User.is_active == True).first()
        
        return {
            "success": True,
            "message": "Admin fixed and test data created",
            "details": results,
            "login": {
                "username": "admin",
                "password": "admin123"
            },
            "admin_active": test_login is not None
        }
        
    except Exception as e:
        logger.error(f"Error in fix-admin: {e}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }