# app/schemas/auth.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    HOTEL_MANAGER = "hotel_manager"
    FRONT_DESK = "front_desk"
    HOUSEKEEPING = "housekeeping"
    MAINTENANCE = "maintenance"
    ACCOUNTING = "accounting"

# Simple user info for login response
class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool

# ==================== AUTHENTICATION ====================
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

class TokenData(BaseModel):
    user_id: int
    username: str
    role: UserRole

# ==================== USER MANAGEMENT ====================
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: UserRole = Field(default=UserRole.FRONT_DESK)
    hotel_id: Optional[int] = None
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: Optional[UserRole] = None
    hotel_id: Optional[int] = None
    is_active: Optional[bool] = None

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v