# app/schemas/maintenance.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MaintenancePriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class MaintenanceStatus(str, Enum):
    REPORTED = "reported"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"
    UNABLE_TO_FIX = "unable_to_fix"

class MaintenanceCategory(str, Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    FURNITURE = "furniture"
    APPLIANCE = "appliance"
    STRUCTURAL = "structural"
    TECHNOLOGY = "technology"
    SAFETY = "safety"
    OTHER = "other"

# Base schema
class MaintenanceRequestBase(BaseModel):
    category: MaintenanceCategory
    priority: MaintenancePriority = MaintenancePriority.NORMAL
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    room_id: Optional[int] = None
    hotel_id: int
    deadline: Optional[datetime] = None

# Schema for creating a request
class MaintenanceRequestCreate(MaintenanceRequestBase):
    reported_by_name: str

# Schema for updating a request
class MaintenanceRequestUpdate(BaseModel):
    category: Optional[MaintenanceCategory] = None
    priority: Optional[MaintenancePriority] = None
    status: Optional[MaintenanceStatus] = None
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=5, max_length=2000)
    assigned_to_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    parts_used: Optional[str] = None
    cost: Optional[float] = Field(default=None, ge=0)
    external_contractor: Optional[str] = None
    contractor_cost: Optional[float] = Field(default=None, ge=0)

# Schema for assignment
class MaintenanceAssign(BaseModel):
    assigned_to_id: int
    notes: Optional[str] = None

# Schema for starting work
class MaintenanceStart(BaseModel):
    notes: Optional[str] = None

# Schema for completing work
class MaintenanceComplete(BaseModel):
    resolution_notes: str
    parts_used: Optional[str] = None
    cost: float = 0.0

# Schema for verifying
class MaintenanceVerify(BaseModel):
    notes: Optional[str] = None

# Response schema
class MaintenanceRequestResponse(MaintenanceRequestBase):
    id: int
    request_number: str
    status: MaintenanceStatus
    reported_by_id: int
    reported_by_name: str
    reported_at: datetime
    assigned_to_id: Optional[int]
    assigned_by_id: Optional[int]
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    verified_at: Optional[datetime]
    resolution_notes: Optional[str]
    parts_used: Optional[str]
    cost: float
    external_contractor: Optional[str]
    contractor_cost: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

# Dashboard stats
class MaintenanceStats(BaseModel):
    total_requests: int
    reported: int
    assigned: int
    in_progress: int
    completed: int
    verified: int
    cancelled: int
    unable_to_fix: int
    by_priority: dict
    by_category: dict
    overdue: int
    avg_completion_time_hours: float