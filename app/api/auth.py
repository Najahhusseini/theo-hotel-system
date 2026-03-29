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
from app.utils.token_blacklist import TokenBlacklist

router = APIRouter(prefix="/auth", tags=["authentication"])

# ==================== LOGIN ====================
@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Find user by username or email
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if account is locked
    if user.is_locked:
        AuditLogger.log_login_attempt(
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="account_locked"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is locked. Contact administrator."
        )
    
    # Check if account is active
    if not user.is_active:
        AuditLogger.log_login_attempt(
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="account_inactive"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
        db.commit()
        
        AuditLogger.log_login_attempt(
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="invalid_password",
            details={"failed_attempts": user.failed_login_attempts}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.last_login = datetime.now()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value
        }
    )
    
    # Log successful login
    AuditLogger.log_login_attempt(
        username=login_data.username,
        success=True,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"user_id": user.id, "role": user.role.value}
    )
    
    # Create user info for response
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

# ==================== REGISTER (Super Admin only) ====================
@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Register a new user. Only Super Admin can create new users.
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        AuditLogger.log_user_management(
            user_id=current_user.id,
            username=current_user.username,
            action="create_user_failed",
            target_user_id=None,
            target_username=user_data.username,
            changes={"error": "username_exists"},
            ip_address=client_ip,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        AuditLogger.log_user_management(
            user_id=current_user.id,
            username=current_user.username,
            action="create_user_failed",
            target_user_id=None,
            target_username=user_data.username,
            changes={"error": "email_exists"},
            ip_address=client_ip,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
        hotel_id=user_data.hotel_id,
        created_by=current_user.id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log user creation
    AuditLogger.log_user_management(
        user_id=current_user.id,
        username=current_user.username,
        action="user_created",
        target_user_id=new_user.id,
        target_username=new_user.username,
        changes={
            "role": new_user.role.value,
            "hotel_id": new_user.hotel_id,
            "email": new_user.email
        },
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Return UserInfo
    return UserInfo(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role,
        is_active=new_user.is_active
    )

# ==================== GET CURRENT USER ====================
@router.get("/me", response_model=UserInfo)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    """
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active
    )

# ==================== UPDATE CURRENT USER ====================
@router.put("/me", response_model=UserInfo)
def update_me(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's information.
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    update_data = user_update.model_dump(exclude_unset=True)
    old_data = {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone
    }
    
    # Prevent users from changing their own role or hotel assignment
    update_data.pop('role', None)
    update_data.pop('hotel_id', None)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Log profile update
    AuditLogger.log_user_management(
        user_id=current_user.id,
        username=current_user.username,
        action="profile_updated",
        target_user_id=current_user.id,
        target_username=current_user.username,
        changes={"old": old_data, "new": update_data},
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active
    )

# ==================== CHANGE PASSWORD ====================
@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        AuditLogger.log_user_management(
            user_id=current_user.id,
            username=current_user.username,
            action="password_change_failed",
            target_user_id=current_user.id,
            target_username=current_user.username,
            changes={"reason": "incorrect_current_password"},
            ip_address=client_ip,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    # Log password change
    AuditLogger.log_user_management(
        user_id=current_user.id,
        username=current_user.username,
        action="password_changed",
        target_user_id=current_user.id,
        target_username=current_user.username,
        changes={"timestamp": datetime.now().isoformat()},
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return {"message": "Password changed successfully"}

# ==================== LOGOUT ====================
@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (blacklist the token).
    """
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
        # Blacklist the token
        TokenBlacklist.blacklist_token(token)
        
        # Log logout
        AuditLogger.log_user_management(
            user_id=current_user.id,
            username=current_user.username,
            action="logout",
            target_user_id=current_user.id,
            target_username=current_user.username,
            changes={"timestamp": datetime.now().isoformat()},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "unknown")
        )
    
    return {"message": "Logged out successfully"}

# ==================== GET ALL USERS (Manager+) ====================
@router.get("/users", response_model=list[UserInfo])
def get_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRoleSchema = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Get all users (Hotel Manager and above).
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    # Hotel managers can only see users from their hotel
    if current_user.role == UserRole.HOTEL_MANAGER and current_user.hotel_id:
        query = query.filter(User.hotel_id == current_user.hotel_id)
    
    users = query.offset(skip).limit(limit).all()
    
    return [
        UserInfo(
            id=u.id,
            username=u.username,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role,
            is_active=u.is_active
        ) for u in users
    ]

# ==================== GET USER BY ID (Manager+) ====================
@router.get("/users/{user_id}", response_model=UserInfo)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Get a specific user by ID (Hotel Manager and above).
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hotel managers can only see users from their hotel
    if current_user.role == UserRole.HOTEL_MANAGER and current_user.hotel_id:
        if user.hotel_id != current_user.hotel_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view users from other hotels"
            )
    
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active
    )

# ==================== UPDATE USER (Manager+) ====================
@router.put("/users/{user_id}", response_model=UserInfo)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hotel_manager)
):
    """
    Update a user (Hotel Manager and above).
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hotel managers can only update users from their hotel
    if current_user.role == UserRole.HOTEL_MANAGER and current_user.hotel_id:
        if user.hotel_id != current_user.hotel_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update users from other hotels"
            )
    
    # Super Admin cannot be modified by Hotel Manager
    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify Super Admin users"
        )
    
    update_data = user_update.model_dump(exclude_unset=True)
    old_data = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "role": user.role.value,
        "hotel_id": user.hotel_id,
        "is_active": user.is_active
    }
    
    # Check if username is taken
    if "username" in update_data and update_data["username"] != user.username:
        existing = db.query(User).filter(User.username == update_data["username"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    # Check if email is taken
    if "email" in update_data and update_data["email"] != user.email:
        existing = db.query(User).filter(User.email == update_data["email"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Log user update
    AuditLogger.log_user_management(
        user_id=current_user.id,
        username=current_user.username,
        action="user_updated",
        target_user_id=user.id,
        target_username=user.username,
        changes={"old": old_data, "new": update_data},
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active
    )

# ==================== DELETE USER (Super Admin only) ====================
@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Delete a user (Soft delete - Super Admin only).
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Log before deletion
    AuditLogger.log_user_management(
        user_id=current_user.id,
        username=current_user.username,
        action="user_deactivated",
        target_user_id=user.id,
        target_username=user.username,
        changes={
            "was_active": user.is_active,
            "deactivated_by": current_user.username
        },
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Soft delete
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.username} deactivated successfully"}