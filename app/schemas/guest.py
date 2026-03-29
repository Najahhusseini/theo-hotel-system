# app/schemas/guest.py
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime, date
from typing import Optional, Dict, Any
import re

class GuestBase(BaseModel):
    """Base guest schema"""
    first_name: str = Field(..., min_length=1, max_length=50, example="John")
    last_name: str = Field(..., min_length=1, max_length=50, example="Smith")
    email: EmailStr = Field(..., example="john.smith@email.com")
    phone: str = Field(..., min_length=5, max_length=20, example="+1234567890")
    alternative_phone: Optional[str] = Field(default=None, max_length=20)
    
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=50)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    
    passport_number: Optional[str] = Field(default=None, max_length=50)
    passport_country: Optional[str] = Field(default=None, max_length=50)
    national_id: Optional[str] = Field(default=None, max_length=50)
    
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    special_notes: Optional[str] = Field(default=None, max_length=1000)
    dietary_restrictions: Optional[str] = Field(default=None, max_length=500)
    accessibility_needs: Optional[str] = Field(default=None, max_length=500)
    
    marketing_consent: bool = False
    email_subscribed: bool = True
    sms_subscribed: bool = False

class GuestCreate(GuestBase):
    """Schema for creating a guest"""
    pass

class GuestUpdate(BaseModel):
    """Schema for updating a guest (all fields optional)"""
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=5, max_length=20)
    alternative_phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=50)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    passport_number: Optional[str] = Field(default=None, max_length=50)
    passport_country: Optional[str] = Field(default=None, max_length=50)
    national_id: Optional[str] = Field(default=None, max_length=50)
    preferences: Optional[Dict[str, Any]] = None
    special_notes: Optional[str] = Field(default=None, max_length=1000)
    dietary_restrictions: Optional[str] = Field(default=None, max_length=500)
    accessibility_needs: Optional[str] = Field(default=None, max_length=500)
    marketing_consent: Optional[bool] = None
    email_subscribed: Optional[bool] = None
    sms_subscribed: Optional[bool] = None
    is_active: Optional[bool] = None
    is_blacklisted: Optional[bool] = None
    blacklist_reason: Optional[str] = Field(default=None, max_length=500)

class GuestResponse(GuestBase):
    """Schema for guest response"""
    id: int
    guest_code: str
    loyalty_level: str
    loyalty_points: int
    total_stays: int
    total_spent: float
    is_active: bool
    is_blacklisted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_stay_date: Optional[date]
    last_interaction: Optional[datetime]
    
    class Config:
        from_attributes = True

class GuestSearchResult(BaseModel):
    """Schema for quick search results"""
    id: int
    guest_code: str
    full_name: str
    email: str
    phone: str
    loyalty_level: str
    total_stays: int