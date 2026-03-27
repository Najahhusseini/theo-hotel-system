# app/models/reservation.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ReservationStatus(str, enum.Enum):
    """Reservation status options"""
    CONFIRMED = "confirmed"      # Booking is confirmed
    CHECKED_IN = "checked_in"    # Guest has arrived
    CHECKED_OUT = "checked_out"  # Guest has departed
    CANCELLED = "cancelled"      # Booking was cancelled
    NO_SHOW = "no_show"          # Guest didn't arrive

class Reservation(Base):
    """Reservation model - represents a booking"""
    __tablename__ = "reservations"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    reservation_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Guest information
    guest_name = Column(String(100), nullable=False)
    guest_email = Column(String(100), nullable=False)
    guest_phone = Column(String(20), nullable=False)
    
    # Reservation details
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    number_of_guests = Column(Integer, default=1)
    total_price = Column(Float, nullable=False)  # Total price for the stay
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.CONFIRMED)
    
    # Special requests
    special_requests = Column(String(500), nullable=True)
    
    # Foreign keys
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=True)  # Link to guest profile
    
    # Relationships
    room = relationship("Room", back_populates="reservations")
    hotel = relationship("Hotel")
    guest = relationship("Guest", back_populates="reservations")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Who created this reservation (will link to users later)
    created_by = Column(String(100), nullable=True)