# main.py - The main FastAPI application
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import os
import logging
import time
from datetime import datetime

from app.core.database import engine, Base, check_db_connection
from app.models import *
from app.websocket.routes import websocket_endpoint
from app.api.monitoring import router as monitoring_router
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

# Setup middleware
from app.utils.request_id import RequestIDMiddleware
from app.utils.cors_config import setup_cors
from app.utils.security_headers import SecurityHeadersMiddleware

# Setup alerts
from app.utils.alerts import send_slack_alert, alert_on_high_latency, alert_on_critical_error

logger = logging.getLogger(__name__)

# Create database tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables created")

# Check database connection
if not check_db_connection():
    logger.error("Database connection failed!")
    send_slack_alert(
        title="Database Connection Failed",
        message="THEO API cannot connect to the database!",
        color="danger"
    )

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

# ==================== MIDDLEWARE ====================
# Add request ID middleware (adds trace ID to every request)
app.add_middleware(RequestIDMiddleware)

# Add CORS middleware
setup_cors(app)

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# ==================== LATENCY MONITORING MIDDLEWARE ====================
@app.middleware("http")
async def latency_monitoring(request: Request, call_next):
    """Monitor request latency and alert on slow responses"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    
    # Add latency header
    response.headers["X-Response-Time-MS"] = str(int(latency_ms))
    
    # Alert on high latency (only in production)
    if os.getenv("ENVIRONMENT") == "production" and latency_ms > 1000:
        alert_on_high_latency(request.url.path, latency_ms)
    
    return response

# ==================== ERROR HANDLING ====================
# Register exception handlers
register_exception_handlers(app)

# Add custom error handler for critical errors
@app.exception_handler(Exception)
async def critical_error_handler(request: Request, exc: Exception):
    """Handle critical errors with Slack alerts"""
    error_id = str(int(time.time()))
    logger.error(f"Critical error {error_id}: {exc}", exc_info=True)
    
    # Send alert for critical errors (only in production)
    if os.getenv("ENVIRONMENT") == "production":
        alert_on_critical_error(exc, {
            "path": request.url.path,
            "method": request.method,
            "error_id": error_id
        })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "error_id": error_id,
            "message": "An unexpected error occurred. Our team has been notified."
        }
    )

# ==================== ROUTERS ====================
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

# Include health and metrics
app.include_router(health.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")

# ==================== WEBSOCKET ====================
@app.websocket("/ws")
async def websocket_route(
    websocket: WebSocket,
    token: str = None,
    client_type: str = "general"
):
    await websocket_endpoint(websocket, token, client_type)

# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    return {
        "message": "Welcome to THEO Hotel Management System",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "status": "operational",
        "database": "postgresql",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics",
        "timestamp": datetime.now().isoformat()
    }

# ==================== STARTUP EVENT ====================
@app.on_event("startup")
async def startup_event():
    logger.info("Starting THEO Hotel Management System...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Version: {os.getenv('APP_VERSION', '1.0.0')}")
    
    # Check database connection
    if check_db_connection():
        logger.info("Database connection successful")
        
        # Send startup notification in production
        if os.getenv("ENVIRONMENT") == "production":
            send_slack_alert(
                title="THEO API Started",
                message=f"Version {os.getenv('APP_VERSION', '1.0.0')} is now running",
                color="good",
                fields=[
                    {"title": "Environment", "value": os.getenv("ENVIRONMENT", "development")},
                    {"title": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                ]
            )
    else:
        logger.error("Database connection failed!")
        if os.getenv("ENVIRONMENT") == "production":
            send_slack_alert(
                title="Database Connection Failed",
                message="THEO API cannot connect to the database!",
                color="danger"
            )

# ==================== SHUTDOWN EVENT ====================
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down THEO Hotel Management System...")
    
    # Close database connections
    engine.dispose()
    logger.info("Database connections closed")
    
    # Send shutdown notification in production
    if os.getenv("ENVIRONMENT") == "production":
        send_slack_alert(
            title="THEO API Shutting Down",
            message="The API is stopping",
            color="warning",
            fields=[
                {"title": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ]
        )