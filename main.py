# main.py - The main FastAPI application
from fastapi import FastAPI, WebSocket
import os
import logging

from app.core.database import engine, Base, check_db_connection
from app.models import *
from app.websocket.routes import websocket_endpoint
from app.api.setup import router as setup_router
from app.api.monitoring import router as monitoring_router
from app.api.one_time_setup import router as one_time_setup_router
from app.api.simple_fix import router as simple_fix_router
from app.api import (
    hotels_router, rooms_router, reservations_router, 
    guests_router, auth_router, housekeeping_router, 
    billing_router, maintenance_router
)
from app.api import health, metrics

# Setup logging
from app.utils.logging_config import setup_logging
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))

# Setup exception handlers
from app.utils.exceptions import register_exception_handlers
from app.utils.cache import redis_client, get_cache_stats
from app.utils.cache_warmup import warmup_cache

# Setup middleware
from app.utils.request_id import RequestIDMiddleware
from app.utils.cors_config import setup_cors
from app.utils.rate_limit import setup_rate_limiting

logger = logging.getLogger(__name__)

# Create database tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables created")

# Create FastAPI app
app = FastAPI(
    title="THEO - Hotel Management System",
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="""
    THEO (The Hotel Enterprise Orchestrator) - A complete hotel management system.
    
    ## Features
    * Hotel management
    * Room management
    * Reservation system
    * Guest CRM with loyalty program
    * Staff authentication and role-based access
    * Housekeeping task management
    * Billing and payments
    * Maintenance request tracking
    * Real-time WebSocket updates
    
    ## Authentication
    Use the `/api/v1/auth/login` endpoint to obtain a JWT token.
    Include the token in the Authorization header: `Bearer <token>`
    
    ## Roles
    - **Super Admin**: Full system access
    - **Hotel Manager**: Hotel-level management
    - **Front Desk**: Reservations, check-in/out
    - **Housekeeping**: Room cleaning tasks
    - **Maintenance**: Issue tracking
    - **Accounting**: Financial operations
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "authentication", "description": "Login and user management"},
        {"name": "hotels", "description": "Hotel management"},
        {"name": "rooms", "description": "Room management"},
        {"name": "reservations", "description": "Booking management"},
        {"name": "guests", "description": "Guest CRM and loyalty"},
        {"name": "housekeeping", "description": "Housekeeping tasks"},
        {"name": "billing", "description": "Financial operations"},
        {"name": "maintenance", "description": "Maintenance requests"},
        {"name": "health", "description": "Health checks"},
        {"name": "metrics", "description": "Prometheus metrics"}
    ]
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
setup_cors(app)
setup_rate_limiting(app)

# Register exception handlers
register_exception_handlers(app)

# Include REST API routers
app.include_router(hotels_router, prefix="/api/v1")
app.include_router(rooms_router, prefix="/api/v1")
app.include_router(reservations_router, prefix="/api/v1")
app.include_router(guests_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(housekeeping_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(maintenance_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(setup_router, prefix="/api/v1")
app.include_router(simple_fix_router, prefix="/api/v1")

# Include health and metrics
app.include_router(health.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(one_time_setup_router, prefix="/api/v1")

# WebSocket route for real-time updates
@app.websocket("/ws")
async def websocket_route(
    websocket: WebSocket,
    token: str = None,
    client_type: str = "general"
):
    await websocket_endpoint(websocket, token, client_type)

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to THEO Hotel Management System",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "status": "operational",
        "database": "postgresql",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("=== STARTUP EVENT STARTED ===")
    logger.info("Starting THEO Hotel Management System...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Version: {os.getenv('APP_VERSION', '1.0.0')}")
    
    # Check database connection
    if check_db_connection():
        logger.info("Database connection successful")
        
        # Warm up cache
        logger.info("Starting cache warmup...")
        try:
            await warmup_cache()
            logger.info("Cache warmup completed successfully")
        except Exception as e:
            logger.error(f"Cache warmup failed: {e}")
    else:
        logger.error("Database connection failed!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down THEO Hotel Management System...")
    engine.dispose()
    logger.info("Database connections closed")