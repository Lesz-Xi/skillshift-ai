"""
Common API utilities and error handling for the FastAPI application.

Provides unified error response schemas and exception handlers to ensure
consistent error formatting across all API endpoints.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response schema for all API endpoints."""
    error: str
    detail: str | None = None


def register_error_handlers(app):
    """
    Register global exception handlers for the FastAPI application.
    
    This ensures consistent error responses across all endpoints:
    - RequestValidationError (Pydantic validation) → 422 
    - ValueError (domain errors) → 400
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors with 422 status code."""
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="ValidationError", 
                detail=str(exc)
            ).model_dump()
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle domain errors (like invalid file paths) with 400 status code."""
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="BadRequest", 
                detail=str(exc)
            ).model_dump()
        )