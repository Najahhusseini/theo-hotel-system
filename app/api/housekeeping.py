# app/api/housekeeping.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models.housekeeping import HousekeepingTask, TaskStatus, TaskPriority, TaskType
from app.models.room import Room, RoomStatus as RoomStatusModel
from app.models.user import User, UserRole
from app.schemas.housekeeping import (
    HousekeepingTaskCreate, HousekeepingTaskUpdate, HousekeepingTaskResponse,
    TaskAssign, TaskStart, TaskComplete, TaskIssue, TaskVerify,
    HousekeepingStats
)
from app.utils.dependencies import (
    get_current_user, require_housekeeping, require_hotel_manager
)

router = APIRouter(prefix="/housekeeping", tags=["housekeeping"])

def generate_task_number():
    """Generate a unique task number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"TASK-{timestamp}-{unique_id}"

def create_checkout_task(room_id: int, hotel_id: int, db: Session) -> HousekeepingTask:
    """Auto-create a checkout cleaning task"""
    task = HousekeepingTask(
        task_number=generate_task_number(),
        task_type=TaskType.CHECKOUT_CLEAN,
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        room_id=room_id,
        hotel_id=hotel_id,
        deadline=datetime.now() + timedelta(hours=2),  # Due in 2 hours
        created_at=datetime.now()
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

# ==================== CREATE TASK ====================
@router.post("/tasks", response_model=HousekeepingTaskResponse, status_code=201)
def create_task(
    task: HousekeepingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)  # Only managers can create tasks
):
    """
    Create a new housekeeping task (Managers only)
    """
    # Check if room exists
    room = db.query(Room).filter(Room.id == task.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Create task
    new_task = HousekeepingTask(
        task_number=generate_task_number(),
        task_type=task.task_type,
        priority=task.priority,
        status=TaskStatus.PENDING,
        room_id=task.room_id,
        hotel_id=task.hotel_id,
        notes=task.notes,
        special_instructions=task.special_instructions,
        deadline=task.deadline,
        created_by_id=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return new_task

# ==================== GET TASKS ====================
@router.get("/tasks", response_model=List[HousekeepingTaskResponse])
def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    room_id: Optional[int] = Query(None, description="Filter by room"),
    assigned_to: Optional[int] = Query(None, description="Filter by assigned staff"),
    hotel_id: Optional[int] = Query(None, description="Filter by hotel"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tasks with filters (based on user role)
    """
    query = db.query(HousekeepingTask)
    
    # Apply filters
    if status:
        query = query.filter(HousekeepingTask.status == status)
    if priority:
        query = query.filter(HousekeepingTask.priority == priority)
    if room_id:
        query = query.filter(HousekeepingTask.room_id == room_id)
    if assigned_to:
        query = query.filter(HousekeepingTask.assigned_to_id == assigned_to)
    if hotel_id:
        query = query.filter(HousekeepingTask.hotel_id == hotel_id)
    
    # Role-based filtering
    if current_user.role == UserRole.HOUSEKEEPING:
        # Housekeeping staff can only see tasks assigned to them
        query = query.filter(HousekeepingTask.assigned_to_id == current_user.id)
    elif current_user.role == UserRole.HOTEL_MANAGER:
        # Managers can see tasks in their hotel
        if current_user.hotel_id:
            query = query.filter(HousekeepingTask.hotel_id == current_user.hotel_id)
    
    # Order by priority and deadline
    query = query.order_by(
        HousekeepingTask.priority,
        HousekeepingTask.deadline,
        HousekeepingTask.created_at
    )
    
    tasks = query.offset(skip).limit(limit).all()
    
    # Add assigned_to_name for response
    result = []
    for task in tasks:
        task_dict = task.__dict__
        if task.assigned_to_id:
            assigned_user = db.query(User).filter(User.id == task.assigned_to_id).first()
            task_dict['assigned_to_name'] = f"{assigned_user.first_name} {assigned_user.last_name}" if assigned_user else None
        result.append(task_dict)
    
    return tasks

# ==================== GET MY TASKS ====================
@router.get("/tasks/my", response_model=List[HousekeepingTaskResponse])
def get_my_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_housekeeping)
):
    """
    Get tasks assigned to current user (Housekeeping staff)
    """
    query = db.query(HousekeepingTask).filter(
        HousekeepingTask.assigned_to_id == current_user.id
    )
    
    if status:
        query = query.filter(HousekeepingTask.status == status)
    
    tasks = query.order_by(
        HousekeepingTask.priority,
        HousekeepingTask.deadline
    ).all()
    
    return tasks

# ==================== ASSIGN TASK ====================
@router.put("/tasks/{task_id}/assign", response_model=HousekeepingTaskResponse)
def assign_task(
    task_id: int,
    assign_data: TaskAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)  # Only managers can assign
):
    """
    Assign a task to a housekeeping staff member (Managers only)
    """
    task = db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if staff exists
    staff = db.query(User).filter(
        User.id == assign_data.assigned_to_id,
        User.role == UserRole.HOUSEKEEPING,
        User.is_active == True
    ).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Housekeeping staff not found")
    
    task.assigned_to_id = assign_data.assigned_to_id
    task.assigned_by_id = current_user.id
    task.assigned_at = datetime.now()
    task.status = TaskStatus.PENDING
    
    db.commit()
    db.refresh(task)
    
    return task

# ==================== START TASK ====================
@router.put("/tasks/{task_id}/start", response_model=HousekeepingTaskResponse)
def start_task(
    task_id: int,
    start_data: TaskStart = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_housekeeping)
):
    """
    Start working on a task (Housekeeping staff only)
    """
    task = db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify task is assigned to current user
    if task.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Task not assigned to you")
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Task already {task.status}")
    
    task.status = TaskStatus.IN_PROGRESS
    task.started_at = datetime.now()
    if start_data and start_data.notes:
        task.notes = start_data.notes
    
    db.commit()
    db.refresh(task)
    
    return task

# ==================== COMPLETE TASK ====================
@router.put("/tasks/{task_id}/complete", response_model=HousekeepingTaskResponse)
def complete_task(
    task_id: int,
    complete_data: TaskComplete = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_housekeeping)
):
    """
    Complete a task (Housekeeping staff only)
    """
    task = db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify task is assigned to current user
    if task.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Task not assigned to you")
    
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Task not in progress")
    
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    task.completed_by_id = current_user.id
    
    if complete_data:
        if complete_data.supplies_used:
            task.supplies_used = complete_data.supplies_used
        if complete_data.notes:
            task.notes = complete_data.notes
    
    db.commit()
    db.refresh(task)
    
    # Update room status to CLEAN after task completion
    room = db.query(Room).filter(Room.id == task.room_id).first()
    if room:
        room.status = RoomStatusModel.CLEAN
        db.commit()
    
    return task

# ==================== REPORT ISSUE ====================
@router.put("/tasks/{task_id}/issue", response_model=HousekeepingTaskResponse)
def report_issue(
    task_id: int,
    issue_data: TaskIssue,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_housekeeping)
):
    """
    Report an issue with the room (Housekeeping staff only)
    """
    task = db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify task is assigned to current user
    if task.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Task not assigned to you")
    
    task.status = TaskStatus.ISSUE
    task.issue_reported = issue_data.issue_description
    
    db.commit()
    db.refresh(task)
    
    # Update room status to MAINTENANCE
    room = db.query(Room).filter(Room.id == task.room_id).first()
    if room:
        room.status = RoomStatusModel.MAINTENANCE
        db.commit()
    
    return task

# ==================== VERIFY TASK ====================
@router.put("/tasks/{task_id}/verify", response_model=HousekeepingTaskResponse)
def verify_task(
    task_id: int,
    verify_data: TaskVerify = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)  # Only managers can verify
):
    """
    Verify completed task (Managers/Supervisors only)
    """
    task = db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    task.status = TaskStatus.VERIFIED
    task.verified_at = datetime.now()
    task.verified_by_id = current_user.id
    
    if verify_data and verify_data.notes:
        task.notes = verify_data.notes
    
    db.commit()
    db.refresh(task)
    
    # Update room status to INSPECTED
    room = db.query(Room).filter(Room.id == task.room_id).first()
    if room:
        room.status = RoomStatusModel.INSPECTED
        db.commit()
    
    return task

# ==================== DASHBOARD STATS ====================
@router.get("/stats", response_model=HousekeepingStats)
def get_housekeeping_stats(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Get housekeeping dashboard statistics
    """
    query = db.query(HousekeepingTask)
    
    if hotel_id:
        query = query.filter(HousekeepingTask.hotel_id == hotel_id)
    elif current_user.hotel_id:
        query = query.filter(HousekeepingTask.hotel_id == current_user.hotel_id)
    
    # Get counts by status
    tasks = query.all()
    
    total = len(tasks)
    pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    verified = sum(1 for t in tasks if t.status == TaskStatus.VERIFIED)
    issues = sum(1 for t in tasks if t.status == TaskStatus.ISSUE)
    
    # Count overdue tasks (deadline passed and not completed)
    now = datetime.now()
    overdue = sum(1 for t in tasks if t.deadline and t.deadline < now and t.status not in [TaskStatus.COMPLETED, TaskStatus.VERIFIED])
    
    # Count by priority
    by_priority = {
        "urgent": sum(1 for t in tasks if t.priority == TaskPriority.URGENT),
        "high": sum(1 for t in tasks if t.priority == TaskPriority.HIGH),
        "normal": sum(1 for t in tasks if t.priority == TaskPriority.NORMAL),
        "low": sum(1 for t in tasks if t.priority == TaskPriority.LOW)
    }
    
    # Count by type
    by_type = {
        "checkout_clean": sum(1 for t in tasks if t.task_type == TaskType.CHECKOUT_CLEAN),
        "daily_clean": sum(1 for t in tasks if t.task_type == TaskType.DAILY_CLEAN),
        "deep_clean": sum(1 for t in tasks if t.task_type == TaskType.DEEP_CLEAN),
        "supply_restock": sum(1 for t in tasks if t.task_type == TaskType.SUPPLY_RESTOCK),
        "inspection": sum(1 for t in tasks if t.task_type == TaskType.INSPECTION)
    }
    
    return HousekeepingStats(
        total_tasks=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        verified=verified,
        issues=issues,
        overdue=overdue,
        by_priority=by_priority,
        by_type=by_type
    )