# app/utils/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing"""
    
    async def dispatch(self, request, call_next):
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state
        request.state.request_id = request_id
        
        # Add to logger context
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Restore original factory
        logging.setLogRecordFactory(old_factory)
        
        return response