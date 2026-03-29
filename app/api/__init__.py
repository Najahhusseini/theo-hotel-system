# app/api/__init__.py
from app.api.hotels import router as hotels_router
from app.api.rooms import router as rooms_router
from app.api.reservations import router as reservations_router
from app.api.guests import router as guests_router
from app.api.auth import router as auth_router
from app.api.housekeeping import router as housekeeping_router
from app.api.billing import router as billing_router
from app.api.maintenance import router as maintenance_router

__all__ = [
    "hotels_router", 
    "rooms_router", 
    "reservations_router",
    "guests_router",
    "auth_router",
    "housekeeping_router",
    "billing_router",
    "maintenance_router"
]