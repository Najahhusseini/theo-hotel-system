# app/api/rooms.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.room import Room, RoomStatus as RoomStatusModel
from app.models.hotel import Hotel
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomStatus
from app.utils.dependencies import (
    require_view_rooms, require_create_room, 
    require_update_room, require_delete_room, require_update_room_status,
    get_current_user
)
from app.models.user import User
from app.utils.cache import cached

router = APIRouter(prefix="/rooms", tags=["rooms"])

# ==================== CREATE ====================
@router.post("/", response_model=RoomResponse, status_code=201)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_room)
):
    """
    Create a new room in a hotel.
    """
    # Check if hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Check if room number already exists in this hotel
    existing_room = db.query(Room).filter(
        Room.hotel_id == room.hotel_id,
        Room.room_number == room.room_number
    ).first()
    if existing_room:
        raise HTTPException(
            status_code=400, 
            detail=f"Room {room.room_number} already exists in this hotel"
        )
    
    # Create new room
    new_room = Room(**room.model_dump())
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    # Update hotel's total room count
    hotel.total_rooms = db.query(Room).filter(Room.hotel_id == hotel.id).count()
    db.commit()
    
    return new_room

# ==================== READ (All) ====================
@router.get("/", response_model=List[RoomResponse])
def get_rooms(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel ID"),
    status: Optional[RoomStatus] = Query(None, description="Filter by room status"),
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_rooms)
):
    """
    Get all rooms with optional filters.
    """
    query = db.query(Room)
    
    # Apply filters
    if hotel_id:
        query = query.filter(Room.hotel_id == hotel_id)
    if status:
        query = query.filter(Room.status == status)
    if room_type:
        query = query.filter(Room.room_type == room_type)
    
    # Order by hotel and room number
    query = query.order_by(Room.hotel_id, Room.floor, Room.room_number)
    
    # Apply pagination
    rooms = query.offset(skip).limit(limit).all()
    return rooms

# ==================== READ (Available) ====================
@router.get("/available", response_model=List[RoomResponse])
@cached(ttl=300)  # Cache for 5 minutes
def get_available_rooms(
    hotel_id: int = Query(..., description="Hotel ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_rooms)
):
    """
    Get all rooms that are ready for check-in.
    Available rooms are those with status CLEAN or INSPECTED.
    """
    rooms = db.query(Room).filter(
        Room.hotel_id == hotel_id,
        Room.status.in_([RoomStatusModel.CLEAN, RoomStatusModel.INSPECTED])
    ).all()
    
    # Convert to dict for JSON serialization
    result = []
    for room in rooms:
        result.append({
            "id": room.id,
            "room_number": room.room_number,
            "floor": room.floor,
            "room_type": room.room_type.value,
            "status": room.status.value,
            "price_per_night": room.price_per_night,
            "max_occupancy": room.max_occupancy,
            "has_view": room.has_view,
            "description": room.description,
            "hotel_id": room.hotel_id,
            "created_at": room.created_at.isoformat() if room.created_at else None,
            "updated_at": room.updated_at.isoformat() if room.updated_at else None
        })
    
    return result
# ==================== READ (One) ====================
@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_rooms)
):
    """
    Get a specific room by ID.
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

# ==================== UPDATE ====================
@router.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_update: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_room)
):
    """
    Update a room's information.
    Only provided fields will be updated.
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Update only the fields that were provided
    update_data = room_update.model_dump(exclude_unset=True)
    
    # If updating room number, check for duplicates
    if "room_number" in update_data:
        existing = db.query(Room).filter(
            Room.hotel_id == room.hotel_id,
            Room.room_number == update_data["room_number"],
            Room.id != room_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Room {update_data['room_number']} already exists in this hotel"
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    
    return room

# ==================== UPDATE STATUS ====================
@router.put("/{room_id}/status", response_model=RoomResponse)
def update_room_status(
    room_id: int,
    status: RoomStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_room_status)
):
    """
    Update just the room status (most common operation).
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    old_status = room.status
    room.status = status
    db.commit()
    db.refresh(room)
    
    print(f"Room {room.room_number} status changed from {old_status} to {status}")
    
    return room

# ==================== DELETE ====================
@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_delete_room)
):
    """
    Delete a room permanently.
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Store hotel_id for updating count
    hotel_id = room.hotel_id
    
    # Delete the room
    db.delete(room)
    db.commit()
    
    # Update hotel's total room count
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if hotel:
        hotel.total_rooms = db.query(Room).filter(Room.hotel_id == hotel_id).count()
        db.commit()
    
    return {"message": f"Room {room.room_number} deleted successfully"}