"""
Rate Limiting Middleware

FastAPI middleware for automatic API rate limiting:
- Per-IP rate limiting
- Per-user rate limiting
- Endpoint-specific limits
- Rate limit headers (X-RateLimit-*)
- 429 Too Many Requests responses

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import logging

from utils.rate_limiter import (
    get_rate_limiter,
    RateLimitManager,
    RateLimitRule
)

logger = logging.getLogger(__name__)


# === Rate Limit Middleware ===

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic rate limiting

    Applies rate limits based on client IP and adds rate limit headers
    """

    # Endpoint mappings (path prefix -> rule name)
    ENDPOINT_RULES = {
        '/api/search': 'search',
        '/api/rag': 'rag',
        '/api/documents': 'documents',
        '/api/batch': 'batch',
        '/api/nlp': 'global',
        '/api/compliance': 'global'
    }

    # Paths to exclude from rate limiting
    EXCLUDE_PATHS = {
        '/health',
        '/docs',
        '/redoc',
        '/openapi.json',
        '/'
    }

    def __init__(
        self,
        app,
        rate_limiter: Optional[RateLimitManager] = None,
        enable_rate_limiting: bool = True
    ):
        """
        Initialize rate limit middleware

        Args:
            app: FastAPI application
            rate_limiter: Optional RateLimitManager instance
            enable_rate_limiting: Whether to enforce rate limits
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_rate_limiter()
        self.enable_rate_limiting = enable_rate_limiting

        logger.info(f"Rate limiting middleware initialized (enabled: {enable_rate_limiting})")

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique client identifier

        Uses: User ID (if authenticated) > X-Forwarded-For > Client IP

        Args:
            request: FastAPI request

        Returns:
            Client identifier string
        """
        # TODO: When authentication is added, check for user ID
        # user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
        # if user_id:
        #     return f"user:{user_id}"

        # Check X-Forwarded-For header (behind proxy/load balancer)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take first IP in chain
            return forwarded_for.split(',')[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        # Last resort
        return 'unknown'

    def _get_endpoint_rule(self, path: str) -> str:
        """
        Determine which rate limit rule to apply

        Args:
            path: Request path

        Returns:
            Rule name
        """
        for prefix, rule_name in self.ENDPOINT_RULES.items():
            if path.startswith(prefix):
                return rule_name

        return 'global'

    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if path should skip rate limiting"""
        # Exact path match
        if path in self.EXCLUDE_PATHS:
            return True

        # Prefix match
        for excluded in self.EXCLUDE_PATHS:
            if path.startswith(excluded):
                return True

        return False

    def _add_rate_limit_headers(
        self,
        response: Response,
        limit_info: dict
    ):
        """
        Add rate limit headers to response

        Headers:
        - X-RateLimit-Limit: Total requests allowed
        - X-RateLimit-Remaining: Requests remaining
        - X-RateLimit-Reset: Unix timestamp when limit resets
        - Retry-After: Seconds until retry (only when blocked)
        """
        response.headers['X-RateLimit-Limit'] = str(limit_info.get('limit', 0))
        response.headers['X-RateLimit-Remaining'] = str(limit_info.get('remaining', 0))

        if 'reset_at' in limit_info:
            response.headers['X-RateLimit-Reset'] = str(int(limit_info['reset_at']))

        if not limit_info.get('allowed', True) and 'retry_after' in limit_info:
            response.headers['Retry-After'] = str(limit_info['retry_after'])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""

        # Skip if rate limiting disabled
        if not self.enable_rate_limiting:
            return await call_next(request)

        # Skip excluded paths
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_identifier(request)

        # Get endpoint rule
        endpoint_rule = self._get_endpoint_rule(request.url.path)

        # Check rate limit
        allowed, limit_info = self.rate_limiter.check(
            identifier=client_id,
            endpoint=endpoint_rule
        )

        # Log rate limit check
        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {client_id} on {request.url.path}",
                extra={
                    'client_id': client_id,
                    'endpoint': endpoint_rule,
                    'path': request.url.path,
                    'retry_after': limit_info.get('retry_after', 0)
                }
            )

        # If rate limit exceeded, return 429
        if not allowed:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    'error': 'Rate limit exceeded',
                    'message': f"Too many requests. Try again in {limit_info.get('retry_after', 0)} seconds.",
                    'limit': limit_info.get('limit', 0),
                    'retry_after': limit_info.get('retry_after', 0)
                }
            )

            self._add_rate_limit_headers(response, limit_info)
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        self._add_rate_limit_headers(response, limit_info)

        return response


# === Rate Limit Decorator ===

def rate_limit(
    requests: int,
    window_seconds: int,
    key_func: Optional[Callable] = None
):
    """
    Decorator for custom rate limits on specific endpoints

    Args:
        requests: Number of requests allowed
        window_seconds: Time window in seconds
        key_func: Optional function to extract client identifier
    """
    import functools

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request = kwargs.get('request')

            if not request:
                # No request object, skip rate limiting
                return await func(*args, **kwargs)

            # Get rate limiter
            limiter = get_rate_limiter()

            # Get client identifier
            if key_func:
                client_id = key_func(request)
            else:
                # Use IP address
                client_id = request.client.host if request.client else 'unknown'

            # Create custom rule
            rule = RateLimitRule(
                requests=requests,
                window_seconds=window_seconds,
                key_prefix=f"custom:{func.__name__}"
            )

            # Check limit
            allowed, info = limiter.limiter.check_limit(client_id, rule)

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        'error': 'Rate limit exceeded',
                        'message': f"Too many requests. Try again in {info.get('retry_after', 0)} seconds.",
                        'limit': info.get('limit', 0),
                        'retry_after': info.get('retry_after', 0)
                    }
                )

            # Call original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# === Rate Limit Configuration Helpers ===

def configure_rate_limits(
    rate_limiter: RateLimitManager,
    custom_limits: dict
):
    """
    Configure custom rate limits

    Args:
        rate_limiter: RateLimitManager instance
        custom_limits: Dict of {endpoint: (requests, window_seconds)}
    """
    for endpoint, (requests, window_seconds) in custom_limits.items():
        rule = RateLimitRule(
            requests=requests,
            window_seconds=window_seconds
        )
        rate_limiter.add_rule(endpoint, rule)

        logger.info(f"Configured rate limit for '{endpoint}': {rule}")


# === Example Usage ===

if __name__ == "__main__":
    from fastapi import FastAPI, Request

    app = FastAPI()

    # Initialize rate limiter
    limiter = get_rate_limiter()

    # Add custom rate limits
    configure_rate_limits(limiter, {
        'expensive_endpoint': (5, 60),  # 5 requests per minute
        'bulk_operation': (2, 300)  # 2 requests per 5 minutes
    })

    # Add middleware
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=limiter,
        enable_rate_limiting=True
    )

    @app.get("/api/search")
    async def search(request: Request):
        """Example endpoint with automatic rate limiting"""
        return {"message": "Search results"}

    @app.post("/api/expensive")
    @rate_limit(requests=5, window_seconds=60)
    async def expensive_operation(request: Request):
        """Example endpoint with custom rate limit decorator"""
        return {"message": "Expensive operation completed"}

    print("Rate limiting middleware ready!")
