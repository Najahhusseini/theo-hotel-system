# app/utils/rate_limit.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple
import os
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Advanced rate limiter with different limits for different endpoints.
    Prevents brute force attacks and API abuse.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        
        Args:
            key: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed in the window
            window: Time window in seconds (default: 60)
        
        Returns:
            (allowed, remaining_requests)
        """
        now = time.time()
        window_ago = now - window
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > window_ago]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False, 0
        
        # Add current request
        self.requests[key].append(now)
        remaining = limit - len(self.requests[key])
        return True, remaining

# Create rate limiters for different endpoints
rate_limiters = {
    "login": RateLimiter(),        # Stricter for login
    "api": RateLimiter(),          # Standard API
    "admin": RateLimiter(),        # Admin operations
    "public": RateLimiter()        # Public endpoints
}

# Rate limits per minute
RATE_LIMITS = {
    "login": {
        "limit": 5,          # 5 attempts per minute
        "window": 60,        # 60 seconds
        "message": "Too many login attempts. Please try again later."
    },
    "api": {
        "limit": 100,        # 100 requests per minute
        "window": 60,
        "message": "Rate limit exceeded. Please slow down."
    },
    "admin": {
        "limit": 50,         # 50 admin operations per minute
        "window": 60,
        "message": "Admin rate limit exceeded."
    },
    "public": {
        "limit": 30,         # 30 public requests per minute
        "window": 60,
        "message": "Too many requests. Please try again."
    }
}

def get_rate_limit_category(path: str) -> str:
    """Determine which rate limit category applies to the request"""
    if "/auth/login" in path:
        return "login"
    elif "/admin" in path or "/monitoring" in path:
        return "admin"
    elif "/public" in path or "/health" in path:
        return "public"
    else:
        return "api"

def rate_limit_middleware(request: Request):
    """Middleware to apply rate limiting"""
    client_ip = request.client.host
    path = request.url.path
    
    # Skip rate limiting for health checks
    if path == "/health" or path == "/api/v1/health":
        return
    
    category = get_rate_limit_category(path)
    limiter = rate_limiters[category]
    limits = RATE_LIMITS[category]
    
    # Use IP as key for now (could also use user ID when authenticated)
    key = client_ip
    
    allowed, remaining = limiter.is_allowed(key, limits["limit"], limits["window"])
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
        raise HTTPException(
            status_code=429,
            detail=limits["message"]
        )
    
    # Add rate limit headers
    return {"remaining": remaining, "limit": limits["limit"]}