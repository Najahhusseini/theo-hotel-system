# app/models/guest.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Date, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Guest(Base):
    """Guest model - comprehensive guest profile like luxury hotels"""
    __tablename__ = "guests"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    guest_code = Column(String(20), unique=True, nullable=False, index=True)  # Unique guest identifier
    
    # Personal information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    alternative_phone = Column(String(20), nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Identification (for compliance)
    passport_number = Column(String(50), nullable=True)
    passport_country = Column(String(50), nullable=True)
    national_id = Column(String(50), nullable=True)
    
    # Loyalty program
    loyalty_level = Column(String(20), default="Bronze")  # Bronze, Silver, Gold, Platinum
    loyalty_points = Column(Integer, default=0)
    total_stays = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    # Preferences (stored as JSON for flexibility)
    preferences = Column(JSON, default=dict)  # e.g., {"pillow_type": "feather", "floor_preference": "high", "room_location": "quiet"}
    
    # Special notes
    special_notes = Column(Text, nullable=True)  # VIP notes, allergies, special occasions
    dietary_restrictions = Column(Text, nullable=True)
    accessibility_needs = Column(Text, nullable=True)
    
    # Marketing preferences
    marketing_consent = Column(Boolean, default=False)
    email_subscribed = Column(Boolean, default=True)
    sms_subscribed = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_blacklisted = Column(Boolean, default=False)  # For problematic guests
    blacklist_reason = Column(Text, nullable=True)
    
    # Who created this profile
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_stay_date = Column(Date, nullable=True)
    last_interaction = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    reservations = relationship("Reservation", back_populates="guest")
    
    def get_full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_loyalty_discount(self):
        """Get discount based on loyalty level"""
        discounts = {
            "Bronze": 0,
            "Silver": 5,
            "Gold": 10,
            "Platinum": 15
        }
        return discounts.get(self.loyalty_level, 0)