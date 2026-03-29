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



def setup_rate_limiting(app: FastAPI = None):
    """
    Setup rate limiting for the FastAPI application.
    This function initializes rate limiting middleware.
    
    Args:
        app: FastAPI application instance
    
    Returns:
        True if setup was successful
    """
    logger.info("Setting up rate limiting middleware")
    
    if app:
        # Add rate limiting middleware to FastAPI
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            """Middleware to apply rate limiting to all requests"""
            try:
                # Apply rate limiting
                result = rate_limit_middleware_function(request)
                
                if result and "remaining" in result:
                    # Process the request
                    response = await call_next(request)
                    
                    # Add rate limit headers
                    response.headers["X-RateLimit-Limit"] = str(result.get("limit", 100))
                    response.headers["X-RateLimit-Remaining"] = str(result.get("remaining", 0))
                    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
                    
                    return response
                else:
                    # Continue without rate limit headers
                    return await call_next(request)
                    
            except HTTPException as e:
                # Return rate limit exceeded response
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
            except Exception as e:
                logger.error(f"Rate limit middleware error: {e}")
                return await call_next(request)
        
        logger.info("Rate limiting middleware added successfully")
    
    logger.info(f"Rate limits configured: Login: {RATE_LIMITS['login']['limit']}/min, API: {RATE_LIMITS['api']['limit']}/min")
    return True

def rate_limit_middleware_function(request: Request) -> Dict:
    """
    Apply rate limiting logic to a request.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Dictionary with remaining and limit if allowed
    """
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    
    # Skip rate limiting for health checks and static files
    skip_paths = ["/health", "/api/v1/health", "/docs", "/openapi.json", "/redoc"]
    if any(path.startswith(skip) for skip in skip_paths):
        return {"remaining": 999, "limit": 999}
    
    category = get_rate_limit_category(path)
    limiter = rate_limiters[category]
    limits = RATE_LIMITS[category]
    
    # Use IP as key for rate limiting
    key = f"{category}:{client_ip}"
    
    allowed, remaining = limiter.is_allowed(key, limits["limit"], limits["window"])
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_ip} on {path} (category: {category})")
        raise HTTPException(
            status_code=429,
            detail=limits["message"]
        )
    
    return {"remaining": remaining, "limit": limits["limit"]}

def get_rate_limit_info(client_ip: str = None, category: str = "api") -> Dict:
    """
    Get rate limit information for a client.
    
    Args:
        client_ip: Client IP address
        category: Rate limit category (login, api, admin, public)
    
    Returns:
        Dictionary with rate limit information
    """
    if not client_ip:
        return {"error": "No client IP provided"}
    
    key = f"{category}:{client_ip}"
    limiter = rate_limiters[category]
    limits = RATE_LIMITS[category]
    
    now = time.time()
    window_ago = now - limits["window"]
    
    # Get request timestamps for this client
    timestamps = limiter.requests.get(key, [])
    recent = [t for t in timestamps if t > window_ago]
    
    return {
        "client_ip": client_ip,
        "category": category,
        "limit": limits["limit"],
        "current_requests": len(recent),
        "remaining": max(0, limits["limit"] - len(recent)),
        "window_seconds": limits["window"],
        "reset_in": int(limits["window"] - (now - recent[0])) if recent else 0,
        "message": limits["message"]
    }

def reset_rate_limit(client_ip: str = None, category: str = None):
    """
    Reset rate limit for a client.
    
    Args:
        client_ip: Client IP address (if None, reset all)
        category: Rate limit category (if None, reset all categories)
    """
    if client_ip is None:
        # Reset all
        for limiter in rate_limiters.values():
            limiter.requests.clear()
        logger.info("Reset all rate limits")
        return {"reset": True, "message": "All rate limits reset"}
    
    # Reset specific client
    if category:
        key = f"{category}:{client_ip}"
        if key in rate_limiters[category].requests:
            del rate_limiters[category].requests[key]
        logger.info(f"Reset rate limit for {client_ip} in category {category}")
    else:
        # Reset client across all categories
        for cat, limiter in rate_limiters.items():
            key = f"{cat}:{client_ip}"
            if key in limiter.requests:
                del limiter.requests[key]
        logger.info(f"Reset rate limits for {client_ip} across all categories")
    
    return {"reset": True, "client_ip": client_ip, "category": category}