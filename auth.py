# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, LoginResponse, UserCreate, 
    UserUpdate, ChangePasswordRequest, UserRole as UserRoleSchema, UserInfo
)
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.utils.dependencies import get_current_user, require_super_admin, require_hotel_manager
from app.utils.audit_log import AuditLogger

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    user = db.query(User).filter(
        (User.username == login_data.username) | 
        (User.email == login_data.username)
    ).first()
    
    if not user:
        AuditLogger.log_login_attempt(
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="user_not_found"
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(login_data.password, user.password_hash):
        AuditLogger.log_login_attempt(
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="invalid_password"
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Update last login
    user.last_login = datetime.now()
    db.commit()
    
    # Create token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value
        }
    )
    
    AuditLogger.log_login_attempt(
        username=login_data.username,
        success=True,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"user_id": user.id}
    )
    
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_info
    )

@router.get("/me", response_model=UserInfo)
def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active
    )