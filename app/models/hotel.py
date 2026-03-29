# app/models/hotel.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Hotel(Base):
    """Hotel model - represents a hotel in our system"""
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    total_rooms = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship - this will connect to rooms
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
  
    reservations = relationship("Reservation", back_populates="hotel") 
