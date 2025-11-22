"""
Middleware Package

FastAPI middleware for request processing, validation, and monitoring.
"""

from middleware.validation_middleware import (
    ValidationMiddleware,
    validate_document_input,
    validate_search_query_input,
    sanitize_inputs,
    validate_pagination,
    log_validation_errors,
    RequestValidator,
    format_validation_error_response
)

from middleware.rate_limit_middleware import (
    RateLimitMiddleware,
    rate_limit,
    configure_rate_limits
)

__all__ = [
    # Validation middleware
    'ValidationMiddleware',
    'validate_document_input',
    'validate_search_query_input',
    'sanitize_inputs',
    'validate_pagination',
    'log_validation_errors',
    'RequestValidator',
    'format_validation_error_response',

    # Rate limiting middleware
    'RateLimitMiddleware',
    'rate_limit',
    'configure_rate_limits'
]
