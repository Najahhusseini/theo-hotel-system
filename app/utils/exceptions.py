# app/utils/exceptions.py
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI):
    """Register all exception handlers for the application"""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "details": exc.errors(),
                "message": "Invalid request data. Please check your input."
            }
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle database integrity errors (duplicate keys, foreign key violations)"""
        logger.error(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Database Conflict",
                "message": "This operation would create duplicate data or violate data constraints."
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(request: Request, exc: SQLAlchemyError):
        """Handle general database errors"""
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database Error",
                "message": "An internal database error occurred. Please try again later."
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with proper logging"""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "message": exc.detail
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions"""
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Our team has been notified."
            }
        )