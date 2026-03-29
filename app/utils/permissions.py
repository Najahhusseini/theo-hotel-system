# app/utils/permissions.py
"""Permission constants for role-based access control"""

from app.models.user import UserRole

# Define required roles for each action
class Permissions:
    # Hotel permissions
    VIEW_HOTELS = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    CREATE_HOTEL = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER]
    UPDATE_HOTEL = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER]
    DELETE_HOTEL = [UserRole.SUPER_ADMIN]
    
    # Room permissions
    VIEW_ROOMS = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK, UserRole.HOUSEKEEPING]
    CREATE_ROOM = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER]
    UPDATE_ROOM = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER]
    DELETE_ROOM = [UserRole.SUPER_ADMIN]
    UPDATE_ROOM_STATUS = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.HOUSEKEEPING]
    
    # Guest permissions
    VIEW_GUESTS = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK, UserRole.ACCOUNTING]
    CREATE_GUEST = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    UPDATE_GUEST = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    DELETE_GUEST = [UserRole.SUPER_ADMIN]
    
    # Reservation permissions
    VIEW_RESERVATIONS = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK, UserRole.ACCOUNTING]
    CREATE_RESERVATION = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    UPDATE_RESERVATION = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    DELETE_RESERVATION = [UserRole.SUPER_ADMIN]
    CHECK_IN = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    CHECK_OUT = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    CANCEL_RESERVATION = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK]
    
    # User management permissions
    VIEW_USERS = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER]
    CREATE_USER = [UserRole.SUPER_ADMIN]
    UPDATE_USER = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER]
    DELETE_USER = [UserRole.SUPER_ADMIN]
    
    # Financial permissions
    VIEW_FINANCIAL = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.ACCOUNTING]
    PROCESS_PAYMENT = [UserRole.SUPER_ADMIN, UserRole.HOTEL_MANAGER, UserRole.FRONT_DESK, UserRole.ACCOUNTING]

def check_permission(user_role, allowed_roles):
    """Check if user has permission"""
    return user_role in allowed_roles