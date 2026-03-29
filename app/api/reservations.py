# app/api/reservations.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room, RoomStatus as RoomStatusModel
from app.models.hotel import Hotel
from app.schemas.reservation import ReservationCreate, ReservationUpdate, ReservationResponse, ReservationStatus as ReservationStatusSchema

from app.utils.dependencies import (
    require_view_reservations, require_create_reservation,
    require_update_reservation, require_delete_reservation,
    require_check_in, require_check_out, require_cancel_reservation,
    get_current_user
)
from app.models.user import User

router = APIRouter(prefix="/reservations", tags=["reservations"])

def generate_reservation_number():
    """Generate a unique reservation number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"RES-{timestamp}-{unique_id}"

def calculate_total_price(room_price_per_night: int, check_in: datetime, check_out: datetime) -> float:
    """Calculate total price for the stay"""
    nights = (check_out - check_in).days
    total = room_price_per_night * nights
    return total / 100  # Convert from cents to dollars

def is_room_available(room_id: int, check_in: datetime, check_out: datetime, exclude_reservation_id: Optional[int] = None, db: Session = None):
    """Check if a room is available for the given dates"""
    
    # Get the room
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return False, "Room not found"
    
    # Check if room is in maintenance
    if room.status == RoomStatusModel.MAINTENANCE:
        return False, "Room is under maintenance"
    
    # Check for overlapping reservations
    query = db.query(Reservation).filter(
        Reservation.room_id == room_id,
        Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]),
        or_(
            # New booking starts during an existing booking
            and_(Reservation.check_in_date <= check_in, Reservation.check_out_date > check_in),
            # New booking ends during an existing booking
            and_(Reservation.check_in_date < check_out, Reservation.check_out_date >= check_out),
            # New booking completely contains an existing booking
            and_(Reservation.check_in_date >= check_in, Reservation.check_out_date <= check_out)
        )
    )
    
    # Exclude current reservation if updating
    if exclude_reservation_id:
        query = query.filter(Reservation.id != exclude_reservation_id)
    
    overlapping = query.first()
    
    if overlapping:
        return False, f"Room is already booked from {overlapping.check_in_date} to {overlapping.check_out_date}"
    
    return True, "Room is available"

# ==================== CREATE RESERVATION ====================
@router.post("/", response_model=ReservationResponse, status_code=201)
def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new reservation.
    
    - Checks if room exists
    - Checks if room is available for the dates
    - Calculates total price
    - Generates unique reservation number
    """
    # Check if room exists
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == reservation.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Check if room belongs to hotel
    if room.hotel_id != reservation.hotel_id:
        raise HTTPException(status_code=400, detail="Room does not belong to this hotel")
    
    # Check dates
    if reservation.check_in_date >= reservation.check_out_date:
        raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")
    
    # Check availability
    is_available, message = is_room_available(
        reservation.room_id,
        reservation.check_in_date,
        reservation.check_out_date,
        db=db
    )
    
    if not is_available:
        raise HTTPException(status_code=409, detail=message)
    
    # Calculate total price
    total_price = calculate_total_price(
        room.price_per_night,
        reservation.check_in_date,
        reservation.check_out_date
    )
    
    # Create reservation
    new_reservation = Reservation(
        reservation_number=generate_reservation_number(),
        guest_name=reservation.guest_name,
        guest_email=reservation.guest_email,
        guest_phone=reservation.guest_phone,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        number_of_guests=reservation.number_of_guests,
        total_price=total_price,
        special_requests=reservation.special_requests,
        room_id=reservation.room_id,
        hotel_id=reservation.hotel_id
    )
    
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    
    return new_reservation

# ==================== READ (All Reservations) ====================
@router.get("/", response_model=List[ReservationResponse])
def get_reservations(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel ID"),
    room_id: Optional[int] = Query(None, description="Filter by room ID"),
    status: Optional[ReservationStatusSchema] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by check-in date"),
    end_date: Optional[datetime] = Query(None, description="Filter by check-out date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get all reservations with optional filters.
    """
    query = db.query(Reservation)
    
    # Apply filters
    if hotel_id:
        query = query.filter(Reservation.hotel_id == hotel_id)
    if room_id:
        query = query.filter(Reservation.room_id == room_id)
    if status:
        query = query.filter(Reservation.status == status)
    if start_date:
        query = query.filter(Reservation.check_in_date >= start_date)
    if end_date:
        query = query.filter(Reservation.check_out_date <= end_date)
    
    # Order by check-in date
    query = query.order_by(Reservation.check_in_date)
    
    reservations = query.offset(skip).limit(limit).all()
    return reservations

# ==================== READ (Today's Arrivals) ====================
@router.get("/today/arrivals", response_model=List[ReservationResponse])
def get_today_arrivals(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel ID"),
    db: Session = Depends(get_db)
):
    """
    Get all reservations checking in today.
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    query = db.query(Reservation).filter(
        Reservation.check_in_date >= today,
        Reservation.check_in_date < tomorrow,
        Reservation.status.in_([ReservationStatus.CONFIRMED])
    )
    
    if hotel_id:
        query = query.filter(Reservation.hotel_id == hotel_id)
    
    return query.order_by(Reservation.check_in_date).all()

# ==================== READ (Today's Departures) ====================
@router.get("/today/departures", response_model=List[ReservationResponse])
def get_today_departures(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel ID"),
    db: Session = Depends(get_db)
):
    """
    Get all reservations checking out today.
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    query = db.query(Reservation).filter(
        Reservation.check_out_date >= today,
        Reservation.check_out_date < tomorrow,
        Reservation.status == ReservationStatus.CHECKED_IN
    )
    
    if hotel_id:
        query = query.filter(Reservation.hotel_id == hotel_id)
    
    return query.order_by(Reservation.check_out_date).all()

# ==================== READ (Single Reservation) ====================
@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific reservation by ID.
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return reservation

# ==================== READ (By Reservation Number) ====================
@router.get("/number/{reservation_number}", response_model=ReservationResponse)
def get_reservation_by_number(
    reservation_number: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific reservation by reservation number.
    """
    reservation = db.query(Reservation).filter(Reservation.reservation_number == reservation_number).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return reservation

# ==================== UPDATE RESERVATION ====================
@router.put("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(
    reservation_id: int,
    reservation_update: ReservationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a reservation.
    If dates or room changes, availability is rechecked.
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Prepare update data
    update_data = reservation_update.model_dump(exclude_unset=True)
    
    # Check if dates or room changed - need to verify availability
    check_availability = False
    new_check_in = update_data.get('check_in_date', reservation.check_in_date)
    new_check_out = update_data.get('check_out_date', reservation.check_out_date)
    new_room_id = update_data.get('room_id', reservation.room_id)
    
    if (new_check_in != reservation.check_in_date or 
        new_check_out != reservation.check_out_date or 
        new_room_id != reservation.room_id):
        check_availability = True
    
    if check_availability:
        # Check if new dates are valid
        if new_check_in >= new_check_out:
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")
        
        # Check availability
        is_available, message = is_room_available(
            new_room_id,
            new_check_in,
            new_check_out,
            exclude_reservation_id=reservation_id,
            db=db
        )
        
        if not is_available:
            raise HTTPException(status_code=409, detail=message)
        
        # If room changed, get new room price
        if new_room_id != reservation.room_id:
            new_room = db.query(Room).filter(Room.id == new_room_id).first()
            if not new_room:
                raise HTTPException(status_code=404, detail="New room not found")
            
            # Recalculate total price
            update_data['total_price'] = calculate_total_price(
                new_room.price_per_night,
                new_check_in,
                new_check_out
            )
        else:
            # Recalculate total price with same room
            room = db.query(Room).filter(Room.id == reservation.room_id).first()
            update_data['total_price'] = calculate_total_price(
                room.price_per_night,
                new_check_in,
                new_check_out
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(reservation, field, value)
    
    db.commit()
    db.refresh(reservation)
    
    return reservation

# ==================== CHECK-IN ====================
@router.post("/{reservation_id}/check-in", response_model=ReservationResponse)
def check_in(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    Check in a guest.
    Updates reservation status to CHECKED_IN.
    Updates room status to OCCUPIED.
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if reservation.status != ReservationStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail=f"Cannot check in reservation with status: {reservation.status}")
    
    # Check if it's the right date (allow early check-in within reason)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    check_in_date = reservation.check_in_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if check_in_date > today:
        raise HTTPException(status_code=400, detail="Cannot check in before check-in date")
    
    # Update reservation status
    reservation.status = ReservationStatus.CHECKED_IN
    
    # Update room status
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if room:
        room.status = RoomStatusModel.OCCUPIED
    
    db.commit()
    db.refresh(reservation)
    
    return reservation

# ==================== CHECK-OUT ====================
@router.post("/{reservation_id}/check-out", response_model=ReservationResponse)
def check_out(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    Check out a guest.
    Updates reservation status to CHECKED_OUT.
    Updates room status to DIRTY (needs cleaning).
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if reservation.status != ReservationStatus.CHECKED_IN:
        raise HTTPException(status_code=400, detail=f"Cannot check out reservation with status: {reservation.status}")
    
    # Update reservation status
    reservation.status = ReservationStatus.CHECKED_OUT
    
    # Update room status to dirty (needs cleaning)
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if room:
        room.status = RoomStatusModel.DIRTY
    
    db.commit()
    db.refresh(reservation)
    
    return reservation

# ==================== CANCEL RESERVATION ====================
@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a reservation.
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if reservation.status in [ReservationStatus.CHECKED_IN, ReservationStatus.CHECKED_OUT]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel reservation that is already {reservation.status}")
    
    reservation.status = ReservationStatus.CANCELLED
    db.commit()
    db.refresh(reservation)
    
    return reservation

# ==================== DELETE RESERVATION ====================
@router.delete("/{reservation_id}")
def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a reservation permanently.
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    db.delete(reservation)
    db.commit()
    
    return {"message": "Reservation deleted successfully"}