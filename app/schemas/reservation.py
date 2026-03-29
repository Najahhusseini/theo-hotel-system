# app/schemas/reservation.py
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from typing import Optional
from enum import Enum

class ReservationStatus(str, Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

# Base schema
class ReservationBase(BaseModel):
    guest_name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        example="John Doe",
        description="Full name of the guest"
    )
    guest_email: EmailStr = Field(
        ..., 
        example="john.doe@example.com",
        description="Guest's email address"
    )
    guest_phone: str = Field(
        ..., 
        min_length=1, 
        max_length=20, 
        example="+1234567890",
        description="Guest's contact number"
    )
    check_in_date: datetime = Field(
        ..., 
        example="2024-04-01T14:00:00",
        description="Expected check-in date and time"
    )
    check_out_date: datetime = Field(
        ..., 
        example="2024-04-05T11:00:00",
        description="Expected check-out date and time"
    )
    number_of_guests: int = Field(
        default=1, 
        ge=1, 
        le=10, 
        example=2,
        description="Number of guests staying"
    )
    special_requests: Optional[str] = Field(
        default=None, 
        max_length=500,
        example="Extra pillows, ocean view if available",
        description="Special requests from guest"
    )

# Schema for creating a reservation
class ReservationCreate(ReservationBase):
    room_id: int = Field(..., gt=0, example=1, description="Room ID to book")
    hotel_id: int = Field(..., gt=0, example=1, description="Hotel ID")
    guest_id: Optional[int] = Field(default=None, example=1, description="Guest ID if already in system")

# Schema for updating a reservation
class ReservationUpdate(BaseModel):
    guest_name: Optional[str] = Field(default=None, min_length=1, max_length=100, example="Jane Doe")
    guest_email: Optional[EmailStr] = Field(default=None, example="jane.doe@example.com")
    guest_phone: Optional[str] = Field(default=None, min_length=1, max_length=20, example="+1987654321")
    check_in_date: Optional[datetime] = Field(default=None, example="2024-04-02T15:00:00")
    check_out_date: Optional[datetime] = Field(default=None, example="2024-04-06T11:00:00")
    number_of_guests: Optional[int] = Field(default=None, ge=1, le=10, example=3)
    special_requests: Optional[str] = Field(default=None, max_length=500)
    room_id: Optional[int] = Field(default=None, gt=0, example=2)
    status: Optional[ReservationStatus] = Field(default=None, example="confirmed")
    guest_id: Optional[int] = Field(default=None, example=1)

# Schema for response
class ReservationResponse(ReservationBase):
    id: int = Field(..., example=1)
    reservation_number: str = Field(
        ..., 
        example="RES-202404011430-ABC123",
        description="Unique reservation identifier"
    )
    room_id: int = Field(..., example=1)
    hotel_id: int = Field(..., example=1)
    total_price: float = Field(..., example=450.00)
    status: ReservationStatus = Field(..., example="confirmed")
    guest_id: Optional[int] = Field(default=None, example=1)
    created_at: datetime = Field(..., example="2024-03-20T09:15:00Z")
    updated_at: Optional[datetime] = Field(default=None, example="2024-03-21T10:30:00Z")
    created_by: Optional[str] = Field(default=None, example="frontdesk")
    
    class Config:
        from_attributes = True