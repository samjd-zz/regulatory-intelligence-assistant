"""
Validation Middleware

FastAPI middleware and decorators for automatic request/response validation.

Features:
- Automatic input sanitization
- Request validation
- Response validation
- Error formatting
- Validation logging

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Any, Optional
import logging
import time
import functools

from utils.validators import (
    InputSanitizer,
    QueryValidator,
    DocumentValidator,
    ValidationResult,
    ValidationError
)

logger = logging.getLogger(__name__)


# === Validation Middleware ===

class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic request validation

    Applies input sanitization and basic validation to all requests
    """

    def __init__(self, app, enable_sanitization: bool = True):
        super().__init__(app)
        self.enable_sanitization = enable_sanitization

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with validation"""

        start_time = time.time()

        try:
            # Log request
            logger.info(
                f"Request: {request.method} {request.url.path}",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'client': request.client.host if request.client else 'unknown'
                }
            )

            # Process request
            response = await call_next(request)

            # Log response
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Response: {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    'status_code': response.status_code,
                    'duration_ms': duration_ms
                }
            )

            return response

        except HTTPException as e:
            # HTTP exceptions are expected, just log and re-raise
            logger.warning(f"HTTP {e.status_code}: {e.detail}")
            raise

        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error: {e}", exc_info=True)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'error': 'Internal server error',
                    'message': str(e) if logger.level == logging.DEBUG else 'An error occurred'
                }
            )


# === Validation Decorators ===

def validate_document_input(func: Callable) -> Callable:
    """
    Decorator to validate document input

    Validates title, content, jurisdiction, etc. before processing
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract document data from kwargs
        # This assumes document data is passed as keyword arguments

        # Get parameters
        title = kwargs.get('title')
        content = kwargs.get('content')
        jurisdiction = kwargs.get('jurisdiction')
        document_type = kwargs.get('document_type')
        citation = kwargs.get('citation')
        effective_date = kwargs.get('effective_date')

        # Validate document
        result = DocumentValidator.validate_document(
            title=title or '',
            content=content or '',
            jurisdiction=jurisdiction or '',
            document_type=document_type or '',
            citation=citation,
            effective_date=effective_date
        )

        if not result.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'error': 'Validation failed',
                    'errors': [e.to_dict() for e in result.errors],
                    'warnings': result.warnings
                }
            )

        # Call original function
        return await func(*args, **kwargs)

    return wrapper


def validate_search_query_input(min_length: int = 2, max_length: int = 500):
    """
    Decorator to validate search query input

    Args:
        min_length: Minimum query length
        max_length: Maximum query length
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get query from kwargs
            query = kwargs.get('query')

            if not query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'error': 'Query parameter is required'}
                )

            # Sanitize query
            sanitized_query = InputSanitizer.sanitize_query(query)
            kwargs['query'] = sanitized_query

            # Validate query
            result = QueryValidator.validate_search_query(
                sanitized_query,
                min_length=min_length,
                max_length=max_length
            )

            if not result.valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        'error': 'Invalid search query',
                        'errors': [e.to_dict() for e in result.errors]
                    }
                )

            # Call original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def sanitize_inputs(func: Callable) -> Callable:
    """
    Decorator to automatically sanitize string inputs

    Applies to all string parameters
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Sanitize all string kwargs
        sanitized_kwargs = {}

        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_kwargs[key] = InputSanitizer.sanitize_string(value)
            else:
                sanitized_kwargs[key] = value

        # Call original function with sanitized inputs
        return await func(*args, **sanitized_kwargs)

    return wrapper


def validate_pagination(max_size: int = 100):
    """
    Decorator to validate pagination parameters

    Args:
        max_size: Maximum page size allowed
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            page = kwargs.get('page', 1)
            page_size = kwargs.get('page_size', 20)

            errors = []

            # Validate page
            if not isinstance(page, int) or page < 1:
                errors.append(ValidationError(
                    field='page',
                    message='Page must be a positive integer',
                    value=page
                ))

            # Validate page_size
            if not isinstance(page_size, int) or page_size < 1:
                errors.append(ValidationError(
                    field='page_size',
                    message='Page size must be a positive integer',
                    value=page_size
                ))
            elif page_size > max_size:
                # Auto-clamp to max
                kwargs['page_size'] = max_size
                logger.warning(f"Page size {page_size} exceeds maximum {max_size}, clamped to {max_size}")

            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        'error': 'Invalid pagination parameters',
                        'errors': [e.to_dict() for e in errors]
                    }
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def log_validation_errors(func: Callable) -> Callable:
    """
    Decorator to log validation errors for monitoring

    Useful for tracking common validation failures
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except HTTPException as e:
            # Log validation errors (400 status)
            if e.status_code == status.HTTP_400_BAD_REQUEST:
                logger.warning(
                    f"Validation error in {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'detail': e.detail
                    }
                )

            # Re-raise
            raise

    return wrapper


# === Request Validation Helpers ===

class RequestValidator:
    """Helper class for validating request data"""

    @staticmethod
    def validate_required_fields(
        data: dict,
        required_fields: list
    ) -> ValidationResult:
        """
        Validate that required fields are present

        Args:
            data: Request data
            required_fields: List of required field names

        Returns:
            ValidationResult
        """
        errors = []

        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(ValidationError(
                    field=field,
                    message=f'Field {field} is required',
                    code='MISSING_FIELD'
                ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    @staticmethod
    def validate_field_types(
        data: dict,
        field_types: dict
    ) -> ValidationResult:
        """
        Validate field types

        Args:
            data: Request data
            field_types: Dict mapping field names to expected types

        Returns:
            ValidationResult
        """
        errors = []

        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    errors.append(ValidationError(
                        field=field,
                        message=f'Field {field} must be of type {expected_type.__name__}',
                        value=data[field],
                        code='INVALID_TYPE'
                    ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    @staticmethod
    def validate_field_ranges(
        data: dict,
        field_ranges: dict
    ) -> ValidationResult:
        """
        Validate numeric field ranges

        Args:
            data: Request data
            field_ranges: Dict mapping field names to (min, max) tuples

        Returns:
            ValidationResult
        """
        errors = []

        for field, (min_val, max_val) in field_ranges.items():
            if field in data and data[field] is not None:
                value = data[field]

                if not isinstance(value, (int, float)):
                    continue

                if value < min_val or value > max_val:
                    errors.append(ValidationError(
                        field=field,
                        message=f'Field {field} must be between {min_val} and {max_val}',
                        value=value,
                        code='OUT_OF_RANGE'
                    ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )


# === Error Response Formatter ===

def format_validation_error_response(
    errors: list,
    warnings: list = None
) -> dict:
    """
    Format validation errors for consistent API responses

    Args:
        errors: List of ValidationError objects
        warnings: Optional list of warning messages

    Returns:
        Formatted error response
    """
    return {
        'error': 'Validation failed',
        'error_count': len(errors),
        'errors': [e.to_dict() if hasattr(e, 'to_dict') else str(e) for e in errors],
        'warnings': warnings or []
    }


# === Example Usage ===

if __name__ == "__main__":
    # Example: Using decorators in FastAPI route
    from fastapi import FastAPI, Query

    app = FastAPI()

    @app.get("/search")
    @validate_search_query_input(min_length=3, max_length=500)
    @sanitize_inputs
    @log_validation_errors
    async def search(query: str = Query(...)):
        """Example search endpoint with validation"""
        return {"query": query, "results": []}

    @app.get("/documents")
    @validate_pagination(max_size=100)
    @log_validation_errors
    async def list_documents(page: int = 1, page_size: int = 20):
        """Example pagination endpoint with validation"""
        return {"page": page, "page_size": page_size, "documents": []}

    # Add validation middleware
    app.add_middleware(ValidationMiddleware, enable_sanitization=True)

    print("Validation middleware and decorators ready!")
