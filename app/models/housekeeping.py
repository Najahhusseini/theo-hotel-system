# app/models/housekeeping.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class TaskPriority(str, enum.Enum):
    """Task priority levels"""
    URGENT = "urgent"        # VIP checkout, needs immediate cleaning
    HIGH = "high"            # Check-out today
    NORMAL = "normal"        # Standard cleaning
    LOW = "low"              # Low priority

class TaskStatus(str, enum.Enum):
    """Task status"""
    PENDING = "pending"      # Not started
    IN_PROGRESS = "in_progress"  # Being cleaned
    COMPLETED = "completed"  # Done, ready for inspection
    VERIFIED = "verified"    # Inspected and approved
    ISSUE = "issue"          # Problem reported

class TaskType(str, enum.Enum):
    """Type of housekeeping task"""
    CHECKOUT_CLEAN = "checkout_clean"    # Full cleaning after checkout
    DAILY_CLEAN = "daily_clean"          # Daily service
    DEEP_CLEAN = "deep_clean"            # Deep cleaning
    SUPPLY_RESTOCK = "supply_restock"    # Restock amenities
    INSPECTION = "inspection"            # Supervisor inspection

class HousekeepingTask(Base):
    """Housekeeping task model"""
    __tablename__ = "housekeeping_tasks"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    task_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Task details
    task_type = Column(SQLEnum(TaskType), nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.NORMAL)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    
    # Room assignment
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    
    # Staff assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Task timing
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Task details
    notes = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    issue_reported = Column(Text, nullable=True)
    
    # Supplies used
    supplies_used = Column(Text, nullable=True)  # JSON string of supplies
    
    # Who created this task
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    room = relationship("Room")
    hotel = relationship("Hotel")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    created_by = relationship("User", foreign_keys=[created_by_id])