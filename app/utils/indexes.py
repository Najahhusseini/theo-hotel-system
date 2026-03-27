# app/utils/indexes.py
"""Additional database indexes for performance"""
from sqlalchemy import Index, text

indexes = [
    # Reservations
    Index("idx_reservations_dates", "reservations.check_in_date", "reservations.check_out_date"),
    Index("idx_reservations_status", "reservations.status"),
    Index("idx_reservations_guest", "reservations.guest_id"),
    Index("idx_reservations_room", "reservations.room_id"),
    
    # Rooms
    Index("idx_rooms_status", "rooms.status"),
    Index("idx_rooms_hotel", "rooms.hotel_id"),
    
    # Guests
    Index("idx_guests_email", "guests.email"),
    Index("idx_guests_loyalty", "guests.loyalty_level"),
    
    # Tasks
    Index("idx_tasks_status_priority", "housekeeping_tasks.status", "housekeeping_tasks.priority"),
    Index("idx_tasks_assigned", "housekeeping_tasks.assigned_to_id"),
    
    # Maintenance
    Index("idx_maintenance_status", "maintenance_requests.status"),
    Index("idx_maintenance_priority", "maintenance_requests.priority"),
]