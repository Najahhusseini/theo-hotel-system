# app/api/maintenance.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models.maintenance import (
    MaintenanceRequest, MaintenancePriority, MaintenanceStatus, MaintenanceCategory
)
from app.models.room import Room, RoomStatus
from app.models.user import User, UserRole
from app.schemas.maintenance import (
    MaintenanceRequestCreate, MaintenanceRequestUpdate, MaintenanceRequestResponse,
    MaintenanceAssign, MaintenanceStart, MaintenanceComplete, MaintenanceVerify,
    MaintenanceStats
)
from app.utils.dependencies import (
    get_current_user, require_maintenance, require_hotel_manager
)

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

def generate_request_number():
    """Generate a unique maintenance request number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"MT-{timestamp}-{unique_id}"

# ==================== CREATE REQUEST ====================
@router.post("/requests", response_model=MaintenanceRequestResponse, status_code=201)
def create_request(
    request: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new maintenance request.
    Anyone can report an issue.
    """
    # Check if room exists (if provided)
    if request.room_id:
        room = db.query(Room).filter(Room.id == request.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
    
    # Create request
    new_request = MaintenanceRequest(
        request_number=generate_request_number(),
        category=request.category,
        priority=request.priority,
        title=request.title,
        description=request.description,
        room_id=request.room_id,
        hotel_id=request.hotel_id,
        reported_by_id=current_user.id,
        reported_by_name=request.reported_by_name or current_user.get_full_name(),
        deadline=request.deadline,
        status=MaintenanceStatus.REPORTED
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    # Emit WebSocket event
    try:
        import asyncio
        from app.websocket.events import emit_notification
        asyncio.create_task(emit_notification(
            current_user.id,
            "Maintenance Request Created",
            f"Request #{new_request.request_number}: {new_request.title}",
            "maintenance"
        ))
    except:
        pass
    
    return new_request

# ==================== GET REQUESTS ====================
@router.get("/requests", response_model=List[MaintenanceRequestResponse])
def get_requests(
    status: Optional[MaintenanceStatus] = Query(None, description="Filter by status"),
    priority: Optional[MaintenancePriority] = Query(None, description="Filter by priority"),
    category: Optional[MaintenanceCategory] = Query(None, description="Filter by category"),
    room_id: Optional[int] = Query(None, description="Filter by room"),
    assigned_to: Optional[int] = Query(None, description="Filter by assigned staff"),
    hotel_id: Optional[int] = Query(None, description="Filter by hotel"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get maintenance requests with filters.
    """
    query = db.query(MaintenanceRequest)
    
    # Apply filters
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    if priority:
        query = query.filter(MaintenanceRequest.priority == priority)
    if category:
        query = query.filter(MaintenanceRequest.category == category)
    if room_id:
        query = query.filter(MaintenanceRequest.room_id == room_id)
    if assigned_to:
        query = query.filter(MaintenanceRequest.assigned_to_id == assigned_to)
    if hotel_id:
        query = query.filter(MaintenanceRequest.hotel_id == hotel_id)
    
    # Role-based filtering
    if current_user.role == UserRole.MAINTENANCE:
        # Maintenance staff see requests assigned to them
        query = query.filter(
            or_(
                MaintenanceRequest.assigned_to_id == current_user.id,
                MaintenanceRequest.status == MaintenanceStatus.REPORTED
            )
        )
    elif current_user.role == UserRole.HOTEL_MANAGER and current_user.hotel_id:
        # Managers see requests in their hotel
        query = query.filter(MaintenanceRequest.hotel_id == current_user.hotel_id)
    
    # Order by priority and date
    priority_order = {
        MaintenancePriority.URGENT: 1,
        MaintenancePriority.HIGH: 2,
        MaintenancePriority.NORMAL: 3,
        MaintenancePriority.LOW: 4
    }
    
    requests_list = query.all()
    requests_list.sort(key=lambda x: (priority_order.get(x.priority, 5), x.reported_at))
    
    return requests_list[skip:skip+limit]

# ==================== GET MY REQUESTS ====================
@router.get("/requests/my", response_model=List[MaintenanceRequestResponse])
def get_my_requests(
    status: Optional[MaintenanceStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance)
):
    """
    Get requests assigned to current user (Maintenance staff)
    """
    query = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.assigned_to_id == current_user.id
    )
    
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    
    requests_list = query.order_by(MaintenanceRequest.priority, MaintenanceRequest.reported_at).all()
    return requests_list

# ==================== GET REQUEST ====================
@router.get("/requests/{request_id}", response_model=MaintenanceRequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific maintenance request by ID.
    """
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return request

# ==================== ASSIGN REQUEST ====================
@router.put("/requests/{request_id}/assign", response_model=MaintenanceRequestResponse)
def assign_request(
    request_id: int,
    assign_data: MaintenanceAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Assign a maintenance request to staff (Managers only)
    """
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check if staff exists
    staff = db.query(User).filter(
        User.id == assign_data.assigned_to_id,
        User.role == UserRole.MAINTENANCE,
        User.is_active == True
    ).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Maintenance staff not found")
    
    request.assigned_to_id = assign_data.assigned_to_id
    request.assigned_by_id = current_user.id
    request.assigned_at = datetime.now()
    request.status = MaintenanceStatus.ASSIGNED
    
    if assign_data.notes:
        request.resolution_notes = assign_data.notes
    
    db.commit()
    db.refresh(request)
    
    # Emit WebSocket notification
    try:
        import asyncio
        from app.websocket.events import emit_notification
        asyncio.create_task(emit_notification(
            assign_data.assigned_to_id,
            "Maintenance Request Assigned",
            f"You have been assigned request #{request.request_number}: {request.title}",
            "maintenance"
        ))
    except:
        pass
    
    return request

# ==================== START WORK ====================
@router.put("/requests/{request_id}/start", response_model=MaintenanceRequestResponse)
def start_work(
    request_id: int,
    start_data: MaintenanceStart = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance)
):
    """
    Start working on a request (Maintenance staff only)
    """
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Verify request is assigned to current user
    if request.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Request not assigned to you")
    
    if request.status != MaintenanceStatus.ASSIGNED:
        raise HTTPException(status_code=400, detail=f"Request already {request.status}")
    
    request.status = MaintenanceStatus.IN_PROGRESS
    request.started_at = datetime.now()
    
    if start_data and start_data.notes:
        request.resolution_notes = start_data.notes
    
    db.commit()
    db.refresh(request)
    
    return request

# ==================== COMPLETE WORK ====================
@router.put("/requests/{request_id}/complete", response_model=MaintenanceRequestResponse)
def complete_work(
    request_id: int,
    complete_data: MaintenanceComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_maintenance)
):
    """
    Complete a maintenance request (Maintenance staff only)
    """
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Verify request is assigned to current user
    if request.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Request not assigned to you")
    
    if request.status != MaintenanceStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Request not in progress")
    
    request.status = MaintenanceStatus.COMPLETED
    request.completed_at = datetime.now()
    request.resolution_notes = complete_data.resolution_notes
    request.parts_used = complete_data.parts_used
    request.cost = complete_data.cost
    
    db.commit()
    db.refresh(request)
    
    return request

# ==================== VERIFY COMPLETION ====================
@router.put("/requests/{request_id}/verify", response_model=MaintenanceRequestResponse)
def verify_completion(
    request_id: int,
    verify_data: MaintenanceVerify = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Verify completed request (Managers only)
    """
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != MaintenanceStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Request not completed yet")
    
    request.status = MaintenanceStatus.VERIFIED
    request.verified_at = datetime.now()
    
    if verify_data and verify_data.notes:
        request.resolution_notes = verify_data.notes
    
    db.commit()
    db.refresh(request)
    
    # Update room status if room was in maintenance
    if request.room_id:
        room = db.query(Room).filter(Room.id == request.room_id).first()
        if room and room.status == RoomStatus.MAINTENANCE:
            room.status = RoomStatus.DIRTY  # Needs cleaning after repair
            db.commit()
    
    return request

# ==================== CANCELLED REQUEST ====================
@router.put("/requests/{request_id}/cancel")
def cancel_request(
    request_id: int,
    reason: str = Query(..., description="Reason for cancellation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Cancel a maintenance request (Managers only)
    """
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = MaintenanceStatus.CANCELLED
    request.resolution_notes = f"CANCELLED: {reason}"
    
    db.commit()
    
    return {"message": "Request cancelled", "request_number": request.request_number}

# ==================== DASHBOARD STATS ====================
@router.get("/stats", response_model=MaintenanceStats)
def get_maintenance_stats(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Get maintenance dashboard statistics
    """
    query = db.query(MaintenanceRequest)
    
    if hotel_id:
        query = query.filter(MaintenanceRequest.hotel_id == hotel_id)
    elif current_user.hotel_id:
        query = query.filter(MaintenanceRequest.hotel_id == current_user.hotel_id)
    
    requests_list = query.all()
    
    total = len(requests_list)
    reported = sum(1 for r in requests_list if r.status == MaintenanceStatus.REPORTED)
    assigned = sum(1 for r in requests_list if r.status == MaintenanceStatus.ASSIGNED)
    in_progress = sum(1 for r in requests_list if r.status == MaintenanceStatus.IN_PROGRESS)
    completed = sum(1 for r in requests_list if r.status == MaintenanceStatus.COMPLETED)
    verified = sum(1 for r in requests_list if r.status == MaintenanceStatus.VERIFIED)
    cancelled = sum(1 for r in requests_list if r.status == MaintenanceStatus.CANCELLED)
    unable = sum(1 for r in requests_list if r.status == MaintenanceStatus.UNABLE_TO_FIX)
    
    # Count by priority
    by_priority = {
        "urgent": sum(1 for r in requests_list if r.priority == MaintenancePriority.URGENT),
        "high": sum(1 for r in requests_list if r.priority == MaintenancePriority.HIGH),
        "normal": sum(1 for r in requests_list if r.priority == MaintenancePriority.NORMAL),
        "low": sum(1 for r in requests_list if r.priority == MaintenancePriority.LOW)
    }
    
    # Count by category
    by_category = {
        "plumbing": sum(1 for r in requests_list if r.category == MaintenanceCategory.PLUMBING),
        "electrical": sum(1 for r in requests_list if r.category == MaintenanceCategory.ELECTRICAL),
        "hvac": sum(1 for r in requests_list if r.category == MaintenanceCategory.HVAC),
        "furniture": sum(1 for r in requests_list if r.category == MaintenanceCategory.FURNITURE),
        "appliance": sum(1 for r in requests_list if r.category == MaintenanceCategory.APPLIANCE),
        "structural": sum(1 for r in requests_list if r.category == MaintenanceCategory.STRUCTURAL),
        "technology": sum(1 for r in requests_list if r.category == MaintenanceCategory.TECHNOLOGY),
        "safety": sum(1 for r in requests_list if r.category == MaintenanceCategory.SAFETY),
        "other": sum(1 for r in requests_list if r.category == MaintenanceCategory.OTHER)
    }
    
    # Count overdue (deadline passed and not completed)
    now = datetime.now()
    overdue = sum(1 for r in requests_list if r.deadline and r.deadline < now and r.status not in [MaintenanceStatus.COMPLETED, MaintenanceStatus.VERIFIED, MaintenanceStatus.CANCELLED])
    
    # Average completion time
    completed_requests = [r for r in requests_list if r.completed_at and r.reported_at]
    avg_time = 0
    if completed_requests:
        total_time = sum((r.completed_at - r.reported_at).total_seconds() / 3600 for r in completed_requests)
        avg_time = total_time / len(completed_requests)
    
    return MaintenanceStats(
        total_requests=total,
        reported=reported,
        assigned=assigned,
        in_progress=in_progress,
        completed=completed,
        verified=verified,
        cancelled=cancelled,
        unable_to_fix=unable,
        by_priority=by_priority,
        by_category=by_category,
        overdue=overdue,
        avg_completion_time_hours=round(avg_time, 1)
    )