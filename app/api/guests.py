# app/api/guests.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, date
import uuid

from app.core.database import get_db
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.schemas.guest import GuestCreate, GuestUpdate, GuestResponse, GuestSearchResult

from app.utils.dependencies import (
    require_view_guests, require_create_guest, 
    require_update_guest, require_delete_guest,
    get_current_user
)
from app.models.user import User

router = APIRouter(prefix="/guests", tags=["guests"])

def generate_guest_code():
    """Generate a unique guest code"""
    timestamp = datetime.now().strftime("%Y%m")
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"G{timestamp}-{unique_id}"

# ==================== CREATE GUEST ====================
@router.post("/", response_model=GuestResponse, status_code=201)
def create_guest(
    guest: GuestCreate,
    created_by: Optional[str] = Query(None, description="Staff member creating this profile"),
    db: Session = Depends(get_db)
):
    """
    Create a new guest profile.
    
    - Automatically generates a unique guest code
    - Checks for duplicate email
    - Sets initial loyalty level to Bronze
    """
    # Check if guest with this email already exists
    existing_guest = db.query(Guest).filter(Guest.email == guest.email).first()
    if existing_guest:
        raise HTTPException(status_code=400, detail="Guest with this email already exists")
    
    # Create new guest
    new_guest = Guest(
        guest_code=generate_guest_code(),
        first_name=guest.first_name,
        last_name=guest.last_name,
        email=guest.email,
        phone=guest.phone,
        alternative_phone=guest.alternative_phone,
        address=guest.address,
        city=guest.city,
        country=guest.country,
        postal_code=guest.postal_code,
        passport_number=guest.passport_number,
        passport_country=guest.passport_country,
        national_id=guest.national_id,
        preferences=guest.preferences or {},
        special_notes=guest.special_notes,
        dietary_restrictions=guest.dietary_restrictions,
        accessibility_needs=guest.accessibility_needs,
        marketing_consent=guest.marketing_consent,
        email_subscribed=guest.email_subscribed,
        sms_subscribed=guest.sms_subscribed,
        loyalty_level="Bronze",  # Start all guests at Bronze
        created_by=created_by
    )
    
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    
    return new_guest

# ==================== READ (All Guests) ====================
@router.get("/", response_model=List[GuestResponse])
def get_guests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    loyalty_level: Optional[str] = Query(None, description="Filter by loyalty level"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get all guests with optional filters.
    """
    query = db.query(Guest)
    
    if loyalty_level:
        query = query.filter(Guest.loyalty_level == loyalty_level)
    if is_active is not None:
        query = query.filter(Guest.is_active == is_active)
    
    guests = query.order_by(Guest.last_name, Guest.first_name).offset(skip).limit(limit).all()
    return guests

# ==================== SEARCH GUESTS ====================
@router.get("/search", response_model=List[GuestSearchResult])
def search_guests(
    q: str = Query(..., min_length=2, description="Search query (name, email, phone, guest code)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search guests by name, email, phone, or guest code.
    Perfect for front desk check-in.
    """
    query = db.query(Guest).filter(
        or_(
            Guest.first_name.ilike(f"%{q}%"),
            Guest.last_name.ilike(f"%{q}%"),
            Guest.email.ilike(f"%{q}%"),
            Guest.phone.ilike(f"%{q}%"),
            Guest.guest_code.ilike(f"%{q}%")
        ),
        Guest.is_active == True
    ).limit(limit)
    
    guests = query.all()
    
    return [
        GuestSearchResult(
            id=g.id,
            guest_code=g.guest_code,
            full_name=g.get_full_name(),
            email=g.email,
            phone=g.phone,
            loyalty_level=g.loyalty_level,
            total_stays=g.total_stays
        ) for g in guests
    ]

# ==================== READ (Single Guest) ====================
@router.get("/{guest_id}", response_model=GuestResponse)
def get_guest(
    guest_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific guest by ID.
    """
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    return guest

# ==================== READ (By Email) ====================
@router.get("/email/{email}", response_model=GuestResponse)
def get_guest_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Get a guest by email address.
    """
    guest = db.query(Guest).filter(Guest.email == email).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    return guest

# ==================== READ (Guest History) ====================
@router.get("/{guest_id}/history")
def get_guest_history(
    guest_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete guest history including all past stays.
    """
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Get all reservations for this guest
    reservations = db.query(Reservation).filter(
        Reservation.guest_id == guest_id
    ).order_by(Reservation.check_in_date.desc()).all()
    
    return {
        "guest": guest,
        "total_stays": len(reservations),
        "reservations": [
            {
                "id": r.id,
                "reservation_number": r.reservation_number,
                "check_in": r.check_in_date,
                "check_out": r.check_out_date,
                "room_id": r.room_id,
                "total_price": r.total_price,
                "status": r.status
            } for r in reservations
        ]
    }

# ==================== UPDATE GUEST ====================
@router.put("/{guest_id}", response_model=GuestResponse)
def update_guest(
    guest_id: int,
    guest_update: GuestUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a guest's profile.
    """
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Update only provided fields
    update_data = guest_update.model_dump(exclude_unset=True)
    
    # If updating email, check for duplicates
    if "email" in update_data and update_data["email"] != guest.email:
        existing = db.query(Guest).filter(Guest.email == update_data["email"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    # Apply updates
    for field, value in update_data.items():
        setattr(guest, field, value)
    
    # Update last interaction
    guest.last_interaction = datetime.now()
    
    db.commit()
    db.refresh(guest)
    
    return guest

# ==================== UPDATE LOYALTY ====================
@router.post("/{guest_id}/update-loyalty", response_model=GuestResponse)
def update_loyalty_level(
    guest_id: int,
    db: Session = Depends(get_db)
):
    """
    Auto-update loyalty level based on total stays.
    """
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Determine loyalty level based on stays
    if guest.total_stays >= 50:
        guest.loyalty_level = "Platinum"
    elif guest.total_stays >= 20:
        guest.loyalty_level = "Gold"
    elif guest.total_stays >= 5:
        guest.loyalty_level = "Silver"
    else:
        guest.loyalty_level = "Bronze"
    
    db.commit()
    db.refresh(guest)
    
    return guest

# ==================== ADD STAY RECORD ====================
@router.post("/{guest_id}/add-stay")
def add_stay_record(
    guest_id: int,
    amount_spent: float = Query(..., description="Amount spent during stay"),
    db: Session = Depends(get_db)
):
    """
    Update guest stats after a completed stay.
    Called automatically on check-out.
    """
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Update stats
    guest.total_stays += 1
    guest.total_spent += amount_spent
    guest.last_stay_date = date.today()
    guest.last_interaction = datetime.now()
    
    # Auto-update loyalty
    if guest.total_stays >= 50:
        guest.loyalty_level = "Platinum"
    elif guest.total_stays >= 20:
        guest.loyalty_level = "Gold"
    elif guest.total_stays >= 5:
        guest.loyalty_level = "Silver"
    
    db.commit()
    
    return {
        "message": "Stay recorded successfully",
        "guest": guest.get_full_name(),
        "total_stays": guest.total_stays,
        "total_spent": guest.total_spent,
        "loyalty_level": guest.loyalty_level
    }

# ==================== DELETE GUEST ====================
@router.delete("/{guest_id}")
def delete_guest(
    guest_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a guest (soft delete - marks as inactive).
    """
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Soft delete
    guest.is_active = False
    db.commit()
    
    return {"message": "Guest deactivated successfully"}