# app/schemas/hotel.py
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

# Base schema with examples
class HotelBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        example="Grand Hotel",
        description="Hotel name"
    )
    address: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        example="123 Main Street, City Center",
        description="Physical address of the hotel"
    )
    phone: str = Field(
        ..., 
        min_length=1, 
        max_length=20, 
        example="+1234567890",
        description="Contact phone number with country code"
    )
    email: EmailStr = Field(
        ..., 
        example="contact@grandhotel.com",
        description="Contact email address"
    )
    total_rooms: int = Field(
        default=0, 
        ge=0, 
        example=150,
        description="Total number of rooms in the hotel"
    )

# Schema for creating a hotel
class HotelCreate(HotelBase):
    pass

# Schema for updating a hotel
class HotelUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=100,
        example="Grand Hotel & Resort"
    )
    address: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=500,
        example="456 Ocean Drive, Beachfront"
    )
    phone: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=20,
        example="+1987654321"
    )
    email: Optional[EmailStr] = Field(default=None, example="reservations@grandhotel.com")
    total_rooms: Optional[int] = Field(default=None, ge=0, example=200)
    is_active: Optional[bool] = Field(default=None, example=True)

# Schema for response
class HotelResponse(HotelBase):
    id: int = Field(..., example=1)
    is_active: bool = Field(..., example=True)
    created_at: datetime = Field(..., example="2024-01-15T10:30:00Z")
    updated_at: Optional[datetime] = Field(default=None, example="2024-01-20T15:45:00Z")
    
    class Config:
        from_attributes = True