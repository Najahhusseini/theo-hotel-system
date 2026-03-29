# app/schemas/room.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class RoomStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    DIRTY = "dirty"
    CLEAN = "clean"
    MAINTENANCE = "maintenance"
    INSPECTED = "inspected"

class RoomType(str, Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    PRESIDENTIAL = "presidential"

class RoomBase(BaseModel):
    room_number: str = Field(
        ..., 
        min_length=1, 
        max_length=10, 
        example="101",
        description="Room number (e.g., 101, A201, 15B)"
    )
    floor: int = Field(
        ..., 
        ge=0, 
        le=100, 
        example=1,
        description="Floor number where room is located"
    )
    room_type: RoomType = Field(
        default=RoomType.STANDARD,
        example="deluxe",
        description="Type of room (standard, deluxe, suite, presidential)"
    )
    price_per_night: int = Field(
        ..., 
        gt=0, 
        example=15000,
        description="Price per night in cents (e.g., 15000 = $150.00)"
    )
    max_occupancy: int = Field(
        default=2, 
        ge=1, 
        le=10, 
        example=2,
        description="Maximum number of guests allowed"
    )
    has_view: bool = Field(
        default=False, 
        example=True,
        description="Whether room has ocean/city view"
    )
    description: Optional[str] = Field(
        default=None, 
        max_length=500,
        example="Spacious room with ocean view and king-size bed",
        description="Room description and amenities"
    )

class RoomCreate(RoomBase):
    hotel_id: int = Field(
        ..., 
        gt=0, 
        example=1,
        description="ID of the hotel this room belongs to"
    )

class RoomUpdate(BaseModel):
    room_number: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=10,
        example="102"
    )
    floor: Optional[int] = Field(default=None, ge=0, le=100, example=2)
    room_type: Optional[RoomType] = Field(default=None, example="suite")
    status: Optional[RoomStatus] = Field(default=None, example="occupied")
    price_per_night: Optional[int] = Field(default=None, gt=0, example=25000)
    max_occupancy: Optional[int] = Field(default=None, ge=1, le=10, example=4)
    has_view: Optional[bool] = Field(default=None, example=False)
    description: Optional[str] = Field(default=None, max_length=500)

class RoomResponse(RoomBase):
    id: int = Field(..., example=1)
    status: RoomStatus = Field(..., example="clean")
    hotel_id: int = Field(..., example=1)
    created_at: datetime = Field(..., example="2024-01-15T10:30:00Z")
    updated_at: Optional[datetime] = Field(default=None, example="2024-01-20T15:45:00Z")
    
    class Config:
        from_attributes = True