# app/schemas/user.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from .auth import UserRole

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: UserRole = Field(default=UserRole.FRONT_DESK)
    hotel_id: Optional[int] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True