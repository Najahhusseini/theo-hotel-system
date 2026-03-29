# app/schemas/housekeeping.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    ISSUE = "issue"

class TaskType(str, Enum):
    CHECKOUT_CLEAN = "checkout_clean"
    DAILY_CLEAN = "daily_clean"
    DEEP_CLEAN = "deep_clean"
    SUPPLY_RESTOCK = "supply_restock"
    INSPECTION = "inspection"

# Base schema
class HousekeepingTaskBase(BaseModel):
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    notes: Optional[str] = Field(default=None, max_length=500)
    special_instructions: Optional[str] = Field(default=None, max_length=500)
    deadline: Optional[datetime] = None

# Schema for creating a task
class HousekeepingTaskCreate(HousekeepingTaskBase):
    room_id: int
    hotel_id: int

# Schema for updating a task
class HousekeepingTaskUpdate(BaseModel):
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None
    issue_reported: Optional[str] = None
    supplies_used: Optional[str] = None

# Schema for assigning a task
class TaskAssign(BaseModel):
    assigned_to_id: int

# Schema for starting a task
class TaskStart(BaseModel):
    notes: Optional[str] = None

# Schema for completing a task
class TaskComplete(BaseModel):
    supplies_used: Optional[str] = Field(default=None, description="JSON string of supplies used")
    notes: Optional[str] = None

# Schema for reporting an issue
class TaskIssue(BaseModel):
    issue_description: str = Field(..., min_length=1, max_length=500)

# Schema for verifying a task
class TaskVerify(BaseModel):
    notes: Optional[str] = None

# Response schema
class HousekeepingTaskResponse(HousekeepingTaskBase):
    id: int
    task_number: str
    status: TaskStatus
    room_id: int
    hotel_id: int
    assigned_to_id: Optional[int]
    assigned_to_name: Optional[str] = None
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    verified_at: Optional[datetime]
    issue_reported: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Summary for dashboard
class HousekeepingStats(BaseModel):
    total_tasks: int
    pending: int
    in_progress: int
    completed: int
    verified: int
    issues: int
    overdue: int
    by_priority: dict
    by_type: dict