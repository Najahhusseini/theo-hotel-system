# app/api/hotels.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate, HotelUpdate, HotelResponse
from app.utils.dependencies import (
    require_view_hotels, require_create_hotel, 
    require_update_hotel, require_delete_hotel,
    get_current_user
)
from app.models.user import User

router = APIRouter(prefix="/hotels", tags=["hotels"])

# ==================== CREATE ====================
@router.post("/", response_model=dict, status_code=200)
def create_hotel(
    name: str = Query(..., description="Hotel name"),
    address: str = Query(..., description="Hotel address"),
    phone: str = Query(..., description="Hotel phone number"),
    email: str = Query(..., description="Hotel email"),
    total_rooms: int = Query(0, description="Total number of rooms"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_hotel)  # Hotel Manager+ can create
):
    """
    Create a new hotel in the system
    """
    # Check if hotel with this email already exists
    existing_hotel = db.query(Hotel).filter(Hotel.email == email).first()
    if existing_hotel:
        raise HTTPException(status_code=400, detail="Hotel with this email already exists")
    
    # Create a new hotel object
    new_hotel = Hotel(
        name=name,
        address=address,
        phone=phone,
        email=email,
        total_rooms=total_rooms
    )
    
    # Add to database
    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)
    
    return {
        "message": "Hotel created successfully",
        "hotel": {
            "id": new_hotel.id,
            "name": new_hotel.name,
            "address": new_hotel.address,
            "phone": new_hotel.phone,
            "email": new_hotel.email,
            "total_rooms": new_hotel.total_rooms,
            "is_active": new_hotel.is_active,
            "created_at": new_hotel.created_at
        }
    }

# ==================== READ (All) ====================
@router.get("/", response_model=List[HotelResponse])
def get_hotels(
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_hotels)  # Front Desk+ can view
):
    """
    Get all hotels
    """
    hotels = db.query(Hotel).filter(Hotel.is_active == True).offset(skip).limit(limit).all()
    return hotels

# ==================== READ (One) ====================
@router.get("/{hotel_id}", response_model=HotelResponse)
def get_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_hotels)  # Front Desk+ can view
):
    """
    Get a specific hotel by ID
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    return hotel

# ==================== UPDATE ====================
@router.put("/{hotel_id}", response_model=HotelResponse)
def update_hotel(
    hotel_id: int,
    hotel_update: HotelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_hotel)  # Hotel Manager+ can update
):
    """
    Update a hotel's information
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Update only the fields that were provided
    update_data = hotel_update.model_dump(exclude_unset=True)
    
    # If updating email, check if it's already used
    if "email" in update_data:
        existing = db.query(Hotel).filter(
            Hotel.email == update_data["email"],
            Hotel.id != hotel_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    # Apply updates
    for field, value in update_data.items():
        setattr(hotel, field, value)
    
    db.commit()
    db.refresh(hotel)
    
    return hotel

# ==================== DELETE ====================
@router.delete("/{hotel_id}")
def delete_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_delete_hotel)  # Super Admin only
):
    """
    Delete a hotel (soft delete - marks as inactive)
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Soft delete - just mark as inactive
    hotel.is_active = False
    db.commit()
    
    return {"message": "Hotel deactivated successfully"}