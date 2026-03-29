# app/utils/cors_config.py
from fastapi.middleware.cors import CORSMiddleware
import os

def setup_cors(app):
    """Configure CORS for production"""
    
    # Get allowed origins from environment
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000,http://localhost:8080"
    ).split(",")
    
    # Development origins
    dev_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Combine and deduplicate
    origins = list(set(allowed_origins + dev_origins))
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-Request-ID"
        ],
        expose_headers=[
            "Content-Length",
            "X-Total-Count",
            "X-Request-ID"
        ],
        max_age=86400,  # 24 hours
    )