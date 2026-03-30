from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.models.user import User
from app.models.hotel import Hotel
from app.utils.security import get_password_hash
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/setup", tags=["setup"])
logger = logging.getLogger(__name__)

@router.post("/create-admin")
def create_admin(
    username: str = "admin",
    password: str = "admin123",
    email: str = "admin@theo.com",
    full_name: str = "System Administrator",
    db: Session = Depends(get_db)
):
    """Create admin user (for first-time setup)"""
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == username).first()
        if admin:
            return {
                "status": "exists",
                "message": f"Admin already exists: {admin.username}",
                "username": admin.username
            }

        # Create admin
        admin = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        logger.info(f"Admin user created: {username}")

        return {
            "status": "created",
            "message": "Admin user created successfully",
            "username": username,
            "password": password
        }

    except Exception as e:
        logger.error(f"Error creating admin: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unlock-admin")
def unlock_admin(
    db: Session = Depends(get_db)
):
    """Unlock admin account"""
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            # Unlock the account
            admin.is_active = True
            db.commit()
            logger.info(f"Admin account unlocked: {admin.username}")
            return {
                "status": "success",
                "message": "Admin account unlocked",
                "username": admin.username
            }
        else:
            # Create admin if doesn't exist
            admin = User(
                username="admin",
                email="admin@theo.com",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            return {
                "status": "created",
                "message": "Admin created and unlocked",
                "username": admin.username
            }
    except Exception as e:
        logger.error(f"Error unlocking admin: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-test-data")
def create_test_data(db: Session = Depends(get_db)):
    """Create test hotel and room data"""
    try:
        from app.models.room import Room
        
        # Create hotel if none
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
            db.commit()
            db.refresh(hotel)
            logger.info(f"Created hotel: {hotel.name}")
        
        # Create some rooms if none
        rooms_count = db.query(Room).count()
        if rooms_count == 0 and hotel:
            room_types = ["standard", "deluxe", "suite"]
            for i in range(1, 11):
                room = Room(
                    room_number=f"{100 + i}",
                    room_type=room_types[i % 3],
                    floor=(i % 5) + 1,
                    price_per_night=100 + (i * 10),
                    status="available",
                    capacity=2 + (i % 3),
                    hotel_id=hotel.id
                )
                db.add(room)
            db.commit()
            logger.info(f"Created 10 rooms")
            rooms_count = 10
        
        return {
            "status": "success",
            "hotel": {"id": hotel.id, "name": hotel.name} if hotel else None,
            "rooms_created": rooms_count
        }
    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_setup_status(db: Session = Depends(get_db)):
    """Check system setup status"""
    try:
        users_count = db.query(User).count()
        hotels_count = db.query(Hotel).count()
        admin = db.query(User).filter(User.username == "admin").first()
        
        return {
            "users_count": users_count,
            "hotels_count": hotels_count,
            "has_admin": admin is not None,
            "admin_locked": not admin.is_active if admin else None
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))