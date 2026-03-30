from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.hotel import Hotel
from app.models.room import Room, RoomType, RoomStatus
from app.utils.security import get_password_hash
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

router = APIRouter(prefix="/simple-fix", tags=["setup"])
logger = logging.getLogger(__name__)

@router.get("/fix-everything")
def fix_everything(db: Session = Depends(get_db)):
    """Simple fix for admin and test data"""
    results = []
    
    try:
        # Rollback any pending transaction
        db.rollback()
        
        # 1. Fix admin using direct SQL with correct column names
        try:
            # Check if admin exists
            admin_check = db.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()
            
            # Hash the password
            password_hash = get_password_hash("admin123")
            
            if admin_check:
                # Update existing admin - unlock and update password
                db.execute(text("""
                    UPDATE users 
                    SET is_active = true,
                        is_locked = false,
                        failed_login_attempts = 0,
                        password_hash = :password_hash
                    WHERE username = 'admin'
                """), {"password_hash": password_hash})
                results.append("✅ Updated existing admin - unlocked and password reset")
            else:
                # Create new admin
                db.execute(text("""
                    INSERT INTO users (
                        username, 
                        email, 
                        password_hash,
                        first_name,
                        last_name,
                        role, 
                        is_active,
                        is_locked,
                        failed_login_attempts,
                        created_at
                    )
                    VALUES (
                        :username, 
                        :email, 
                        :password_hash,
                        :first_name,
                        :last_name,
                        :role, 
                        true,
                        false,
                        0,
                        NOW()
                    )
                """), {
                    "username": "admin",
                    "email": "admin@theo.com",
                    "password_hash": password_hash,
                    "first_name": "System",
                    "last_name": "Administrator",
                    "role": UserRole.SUPER_ADMIN.value
                })
                results.append("✅ Created new admin user")
            
            db.commit()
            results.append("✅ Admin fixed successfully")
            
        except Exception as e:
            db.rollback()
            results.append(f"⚠️ Admin fix error: {str(e)[:200]}")
        
        # 2. Create hotel if none exists
        try:
            hotel = db.execute(text("SELECT id FROM hotels LIMIT 1")).fetchone()
            
            if not hotel:
                db.execute(text("""
                    INSERT INTO hotels (name, address, phone, email, total_rooms, is_active, created_at)
                    VALUES (:name, :address, :phone, :email, :total_rooms, true, NOW())
                """), {
                    "name": "Grand Hotel Downtown",
                    "address": "123 Main St, City Center",
                    "phone": "+1234567890",
                    "email": "info@grandhotel.com",
                    "total_rooms": 100
                })
                db.commit()
                results.append("✅ Created test hotel")
                
                # Get the hotel id
                hotel = db.execute(text("SELECT id FROM hotels LIMIT 1")).fetchone()
            else:
                results.append("ℹ️ Hotel already exists")
            
            hotel_id = hotel[0] if hotel else None
            
        except Exception as e:
            db.rollback()
            results.append(f"⚠️ Hotel error: {str(e)[:100]}")
        
        # 3. Create rooms if none exist
        if hotel_id:
            try:
                room_count = db.execute(text("SELECT COUNT(*) FROM rooms WHERE hotel_id = :hotel_id"), {"hotel_id": hotel_id}).fetchone()[0]
                
                if room_count == 0:
                    rooms_data = [
                        ("101", 1, "standard", 15000, 2, False),
                        ("102", 1, "standard", 15000, 2, False),
                        ("201", 2, "deluxe", 25000, 2, True),
                        ("202", 2, "deluxe", 25000, 2, True),
                        ("301", 3, "suite", 40000, 4, True),
                        ("302", 3, "presidential", 80000, 6, True),
                    ]
                    
                    for room_num, floor, r_type, price, occupancy, view in rooms_data:
                        db.execute(text("""
                            INSERT INTO rooms (room_number, floor, room_type, price_per_night, max_occupancy, has_view, status, hotel_id)
                            VALUES (:room_number, :floor, :room_type, :price, :occupancy, :view, 'clean', :hotel_id)
                        """), {
                            "room_number": room_num,
                            "floor": floor,
                            "room_type": r_type,
                            "price": price,
                            "occupancy": occupancy,
                            "view": view,
                            "hotel_id": hotel_id
                        })
                    
                    db.commit()
                    results.append(f"✅ Created {len(rooms_data)} test rooms")
                else:
                    results.append(f"ℹ️ Rooms already exist ({room_count} rooms)")
                    
            except Exception as e:
                db.rollback()
                results.append(f"⚠️ Room error: {str(e)[:100]}")
        
        return {
            "success": True,
            "message": "Fix completed",
            "details": results,
            "login": {
                "username": "admin",
                "password": "admin123"
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "details": results
        }