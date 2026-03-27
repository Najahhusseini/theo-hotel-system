# app/models/room.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class RoomStatus(str, enum.Enum):
    """Room status options - like traffic lights for room readiness"""
    AVAILABLE = "available"      # Green - Ready for guest
    OCCUPIED = "occupied"        # Red - Guest inside
    DIRTY = "dirty"              # Yellow - Needs cleaning
    CLEAN = "clean"              # Green - Clean and ready
    MAINTENANCE = "maintenance"  # Red - Out of service
    INSPECTED = "inspected"      # Blue - Checked by supervisor

class RoomType(str, enum.Enum):
    """Room type options"""
    STANDARD = "standard"        # Basic room
    DELUXE = "deluxe"           # Better view, larger
    SUITE = "suite"             # Separate living area
    PRESIDENTIAL = "presidential"  # Top luxury

class Room(Base):
    """Room model - represents a hotel room"""
    __tablename__ = "rooms"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(10), nullable=False)
    floor = Column(Integer, nullable=False)
    
    # Room characteristics
    room_type = Column(Enum(RoomType), default=RoomType.STANDARD)
    status = Column(Enum(RoomStatus), default=RoomStatus.CLEAN)
    price_per_night = Column(Integer, nullable=False)  # Stored in cents (e.g., $150 = 15000)
    max_occupancy = Column(Integer, default=2)
    has_view = Column(Boolean, default=False)
    description = Column(String(500), nullable=True)
    
    # Which hotel does this room belong to?
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    
    # Relationships
    hotel = relationship("Hotel", back_populates="rooms")
    # reservations relationship
    reservations = relationship("Reservation", back_populates="room", cascade="all, delete-orphan")
    housekeeping_tasks = relationship("HousekeepingTask", back_populates="room")

    # Timestamps for tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())