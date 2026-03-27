# app/utils/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_access_token
from app.utils.permissions import check_permission

# Security scheme for JWT
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_role(required_role: UserRole):
    """Dependency factory to require a specific role"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

def require_permission(allowed_roles: List[UserRole]):
    """Dependency factory to require specific permissions"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not check_permission(current_user.role, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return permission_checker

# Role-based dependencies
require_super_admin = require_role(UserRole.SUPER_ADMIN)
require_hotel_manager = require_role(UserRole.HOTEL_MANAGER)
require_front_desk = require_role(UserRole.FRONT_DESK)
require_housekeeping = require_role(UserRole.HOUSEKEEPING)
require_maintenance = require_role(UserRole.MAINTENANCE)
require_accounting = require_role(UserRole.ACCOUNTING)

# Permission-based dependencies (from permissions.py)
from app.utils.permissions import Permissions

require_view_hotels = require_permission(Permissions.VIEW_HOTELS)
require_create_hotel = require_permission(Permissions.CREATE_HOTEL)
require_update_hotel = require_permission(Permissions.UPDATE_HOTEL)
require_delete_hotel = require_permission(Permissions.DELETE_HOTEL)

require_view_rooms = require_permission(Permissions.VIEW_ROOMS)
require_create_room = require_permission(Permissions.CREATE_ROOM)
require_update_room = require_permission(Permissions.UPDATE_ROOM)
require_delete_room = require_permission(Permissions.DELETE_ROOM)
require_update_room_status = require_permission(Permissions.UPDATE_ROOM_STATUS)

require_view_guests = require_permission(Permissions.VIEW_GUESTS)
require_create_guest = require_permission(Permissions.CREATE_GUEST)
require_update_guest = require_permission(Permissions.UPDATE_GUEST)
require_delete_guest = require_permission(Permissions.DELETE_GUEST)

require_view_reservations = require_permission(Permissions.VIEW_RESERVATIONS)
require_create_reservation = require_permission(Permissions.CREATE_RESERVATION)
require_update_reservation = require_permission(Permissions.UPDATE_RESERVATION)
require_delete_reservation = require_permission(Permissions.DELETE_RESERVATION)
require_check_in = require_permission(Permissions.CHECK_IN)
require_check_out = require_permission(Permissions.CHECK_OUT)
require_cancel_reservation = require_permission(Permissions.CANCEL_RESERVATION)

require_view_users = require_permission(Permissions.VIEW_USERS)
require_create_user = require_permission(Permissions.CREATE_USER)
require_update_user = require_permission(Permissions.UPDATE_USER)
require_delete_user = require_permission(Permissions.DELETE_USER)

require_view_financial = require_permission(Permissions.VIEW_FINANCIAL)
require_process_payment = require_permission(Permissions.PROCESS_PAYMENT)