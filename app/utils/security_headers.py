# app/utils/security_headers.py
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses to protect against common web vulnerabilities.
    These headers are essential for production deployment.
    """
    async def dispatch(self, request: Request, call_next):
    response = await call_next(request)
    
    # Prevent browsers from MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Strict Transport Security (HTTPS only)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Remove Server header (safe way)
    if "Server" in response.headers:
        del response.headers["Server"]
    
    return response
   