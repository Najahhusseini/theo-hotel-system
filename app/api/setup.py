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

@router.get("/status")
def get_setup_status(db: Session = Depends(get_db)):
    """Check if system is set up"""
    users_count = db.query(User).count()
    hotels_count = db.query(Hotel).count()
    
    return {
        "status": "ready" if users_count > 0 else "needs_setup",
        "users_count": users_count,
        "hotels_count": hotels_count,
        "has_admin": db.query(User).filter(User.role == "admin").first() is not None
    }