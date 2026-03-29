# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    """User roles with different permissions"""
    SUPER_ADMIN = "super_admin"      # Full system access
    HOTEL_MANAGER = "hotel_manager"  # Manage hotel settings
    FRONT_DESK = "front_desk"        # Reservations, check-in/out
    HOUSEKEEPING = "housekeeping"    # Room status updates
    MAINTENANCE = "maintenance"      # Issue tracking
    ACCOUNTING = "accounting"        # Billing and invoices

class User(Base):
    """User model - staff accounts"""
    __tablename__ = "users"
    
    # Basic information
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Personal information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.FRONT_DESK)
    
    # Hotel assignment (for multi-hotel systems)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)  # Lock account after failed attempts
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Who created this user
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    hotel = relationship("Hotel")
    created_by_user = relationship("User", remote_side=[id])
    
    def get_full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def has_permission(self, required_role):
        """Check if user has required role permission"""
        role_hierarchy = {
            UserRole.SUPER_ADMIN: 100,
            UserRole.HOTEL_MANAGER: 80,
            UserRole.ACCOUNTING: 70,
            UserRole.FRONT_DESK: 50,
            UserRole.HOUSEKEEPING: 30,
            UserRole.MAINTENANCE: 20
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level