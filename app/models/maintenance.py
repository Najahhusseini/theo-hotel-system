# app/models/maintenance.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class MaintenancePriority(str, enum.Enum):
    """Priority levels for maintenance requests"""
    URGENT = "urgent"      # Immediate attention (safety issue, no water/power)
    HIGH = "high"          # Needs attention today
    NORMAL = "normal"      # Standard maintenance
    LOW = "low"            # Can be scheduled later

class MaintenanceStatus(str, enum.Enum):
    """Status of maintenance requests"""
    REPORTED = "reported"          # Issue reported, not yet assigned
    ASSIGNED = "assigned"          # Assigned to staff
    IN_PROGRESS = "in_progress"    # Staff working on it
    COMPLETED = "completed"        # Fixed, awaiting verification
    VERIFIED = "verified"          # Verified by supervisor
    CANCELLED = "cancelled"        # Cancelled (not needed, duplicate)
    UNABLE_TO_FIX = "unable_to_fix" # Needs external contractor

class MaintenanceCategory(str, enum.Enum):
    """Categories of maintenance issues"""
    PLUMBING = "plumbing"          # Leaks, toilets, pipes
    ELECTRICAL = "electrical"      # Lights, outlets, wiring
    HVAC = "hvac"                  # AC, heating, ventilation
    FURNITURE = "furniture"        # Broken furniture, fixtures
    APPLIANCE = "appliance"        # TV, fridge, microwave
    STRUCTURAL = "structural"      # Walls, ceilings, floors
    TECHNOLOGY = "technology"      # WiFi, TV, phone
    SAFETY = "safety"              # Fire alarm, locks, safety issues
    OTHER = "other"                # Miscellaneous

class MaintenanceRequest(Base):
    """Maintenance request model"""
    __tablename__ = "maintenance_requests"
    
    # Basic identification
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Issue details
    category = Column(SQLEnum(MaintenanceCategory), nullable=False)
    priority = Column(SQLEnum(MaintenancePriority), default=MaintenancePriority.NORMAL)
    status = Column(SQLEnum(MaintenanceStatus), default=MaintenanceStatus.REPORTED)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Location
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)  # Null for common areas
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    
    # Reported by
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_by_name = Column(String(100), nullable=False)
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Work details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    parts_used = Column(Text, nullable=True)  # JSON string of parts used
    cost = Column(Float, default=0.0)  # Cost of parts/labor
    
    # External contractor
    external_contractor = Column(String(200), nullable=True)
    contractor_cost = Column(Float, default=0.0)
    
    # Priority deadlines
    deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    room = relationship("Room")
    hotel = relationship("Hotel")
    reported_by = relationship("User", foreign_keys=[reported_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])