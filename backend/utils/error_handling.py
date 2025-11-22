"""
Enhanced Error Handling and Logging Utilities

Provides standardized error handling, logging, and monitoring
for the Regulatory Intelligence Assistant.

Features:
- Structured logging with context
- Error tracking and reporting
- Performance monitoring
- Request/response logging
- Audit trail support

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import logging
import functools
import time
import traceback
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json


# === Structured Logging ===

class StructuredLogger:
    """
    Structured logger with context support

    Provides consistent logging format with additional context fields
    for better searchability and analysis.
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger

        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log(
        self,
        level: int,
        message: str,
        **context
    ):
        """
        Log message with structured context

        Args:
            level: Log level
            message: Log message
            **context: Additional context fields
        """
        if context:
            context_str = json.dumps(context, default=str)
            full_message = f"{message} | {context_str}"
        else:
            full_message = message

        self.logger.log(level, full_message)

    def info(self, message: str, **context):
        """Info level log"""
        self.log(logging.INFO, message, **context)

    def warning(self, message: str, **context):
        """Warning level log"""
        self.log(logging.WARNING, message, **context)

    def error(self, message: str, **context):
        """Error level log"""
        self.log(logging.ERROR, message, **context)

    def debug(self, message: str, **context):
        """Debug level log"""
        self.log(logging.DEBUG, message, **context)

    def critical(self, message: str, **context):
        """Critical level log"""
        self.log(logging.CRITICAL, message, **context)


# === Performance Monitoring ===

@dataclass
class PerformanceMetrics:
    """Performance metrics for a function call"""
    function_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


def monitor_performance(logger: Optional[StructuredLogger] = None):
    """
    Decorator to monitor function performance

    Args:
        logger: Optional logger instance

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = PerformanceMetrics(
                function_name=func.__name__,
                start_time=datetime.now()
            )

            try:
                result = func(*args, **kwargs)
                metrics.success = True
                return result

            except Exception as e:
                metrics.success = False
                metrics.error = str(e)
                raise

            finally:
                metrics.end_time = datetime.now()
                metrics.duration_ms = (
                    metrics.end_time - metrics.start_time
                ).total_seconds() * 1000

                if logger:
                    logger.info(
                        f"Function {func.__name__} completed",
                        duration_ms=metrics.duration_ms,
                        success=metrics.success,
                        error=metrics.error
                    )

        return wrapper
    return decorator


# === Error Handling ===

@dataclass
class ErrorContext:
    """Context information for errors"""
    timestamp: datetime
    error_type: str
    error_message: str
    function_name: str
    traceback: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_type': self.error_type,
            'error_message': self.error_message,
            'function_name': self.function_name,
            'traceback': self.traceback,
            'user_id': self.user_id,
            'request_id': self.request_id,
            'additional_context': self.additional_context
        }


def handle_errors(
    logger: Optional[StructuredLogger] = None,
    reraise: bool = True,
    default_return: Any = None
):
    """
    Decorator for standardized error handling

    Args:
        logger: Optional logger instance
        reraise: Whether to reraise exceptions
        default_return: Default return value on error

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                error_context = ErrorContext(
                    timestamp=datetime.now(),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    function_name=func.__name__,
                    traceback=traceback.format_exc()
                )

                if logger:
                    logger.error(
                        f"Error in {func.__name__}",
                        error_type=error_context.error_type,
                        error_message=error_context.error_message
                    )

                if reraise:
                    raise
                else:
                    return default_return

        return wrapper
    return decorator


# === Request/Response Logging ===

@dataclass
class RequestLog:
    """Log entry for API requests"""
    timestamp: datetime
    request_id: str
    endpoint: str
    method: str
    user_id: Optional[str] = None
    query_params: Dict[str, Any] = field(default_factory=dict)
    body_params: Dict[str, Any] = field(default_factory=dict)
    response_status: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'request_id': self.request_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'user_id': self.user_id,
            'query_params': self.query_params,
            'body_params': self.body_params,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'error': self.error
        }


def log_request(logger: StructuredLogger):
    """
    Decorator to log API requests

    Args:
        logger: Logger instance

    Returns:
        Decorated function
    """
    import uuid

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            start_time = time.time()

            request_log = RequestLog(
                timestamp=datetime.now(),
                request_id=request_id,
                endpoint=func.__name__,
                method='POST'  # Default, can be enhanced
            )

            try:
                # Log request start
                logger.info(
                    f"Request started: {func.__name__}",
                    request_id=request_id
                )

                # Execute function
                result = func(*args, **kwargs)

                # Log success
                request_log.response_status = 200
                request_log.response_time_ms = (time.time() - start_time) * 1000

                logger.info(
                    f"Request completed: {func.__name__}",
                    request_id=request_id,
                    duration_ms=request_log.response_time_ms,
                    status=200
                )

                return result

            except Exception as e:
                # Log error
                request_log.response_status = 500
                request_log.response_time_ms = (time.time() - start_time) * 1000
                request_log.error = str(e)

                logger.error(
                    f"Request failed: {func.__name__}",
                    request_id=request_id,
                    duration_ms=request_log.response_time_ms,
                    error=str(e)
                )

                raise

        return wrapper
    return decorator


# === Circuit Breaker Pattern ===

class CircuitBreaker:
    """
    Circuit breaker for external service calls

    Prevents cascading failures by temporarily stopping calls
    to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before trying again
            logger: Optional logger
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.logger = logger
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs):
        """
        Call function with circuit breaker protection

        Args:
            func: Function to call
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or call fails
        """
        # Check circuit state
        if self.state == "OPEN":
            time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()

            if time_since_failure < self.timeout_seconds:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
            else:
                # Try half-open
                self.state = "HALF_OPEN"
                if self.logger:
                    self.logger.info(f"Circuit breaker HALF_OPEN for {func.__name__}")

        # Attempt call
        try:
            result = func(*args, **kwargs)

            # Success - reset circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                if self.logger:
                    self.logger.info(f"Circuit breaker CLOSED for {func.__name__}")

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                if self.logger:
                    self.logger.error(
                        f"Circuit breaker OPEN for {func.__name__}",
                        failure_count=self.failure_count
                    )

            raise


# === Retry Logic ===

def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    logger: Optional[StructuredLogger] = None
):
    """
    Decorator to retry failed function calls

    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries
        backoff_multiplier: Multiplier for exponential backoff
        logger: Optional logger

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = delay_seconds

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    attempt += 1

                    if attempt >= max_attempts:
                        if logger:
                            logger.error(
                                f"Max retries exceeded for {func.__name__}",
                                attempts=attempt,
                                error=str(e)
                            )
                        raise

                    if logger:
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__}",
                            delay_seconds=delay,
                            error=str(e)
                        )

                    time.sleep(delay)
                    delay *= backoff_multiplier

        return wrapper
    return decorator


# === Audit Trail ===

@dataclass
class AuditLogEntry:
    """Audit log entry for compliance tracking"""
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }


class AuditLogger:
    """Audit logger for compliance and security"""

    def __init__(self, logger: StructuredLogger):
        """Initialize audit logger"""
        self.logger = logger

    def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        **details
    ):
        """
        Log user action for audit trail

        Args:
            user_id: User identifier
            action: Action performed (e.g., "search", "view", "export")
            resource_type: Type of resource (e.g., "regulation", "answer")
            resource_id: Resource identifier
            **details: Additional details
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )

        self.logger.info(
            f"Audit: {action} on {resource_type}/{resource_id}",
            **entry.to_dict()
        )


# === Example Usage ===

if __name__ == "__main__":
    # Create logger
    logger = StructuredLogger("example")

    # Example 1: Performance monitoring
    @monitor_performance(logger)
    def slow_function():
        time.sleep(0.1)
        return "Done"

    result = slow_function()

    # Example 2: Error handling
    @handle_errors(logger, reraise=False, default_return=None)
    def failing_function():
        raise ValueError("Something went wrong")

    result = failing_function()  # Returns None, logs error

    # Example 3: Retry logic
    @retry(max_attempts=3, delay_seconds=0.5, logger=logger)
    def unstable_function():
        import random
        if random.random() < 0.7:
            raise Exception("Random failure")
        return "Success"

    # Example 4: Circuit breaker
    breaker = CircuitBreaker(failure_threshold=3, logger=logger)

    def external_api_call():
        # Simulated API call
        time.sleep(0.01)
        return "API Response"

    try:
        result = breaker.call(external_api_call)
    except Exception as e:
        print(f"Circuit breaker error: {e}")

    # Example 5: Audit logging
    audit_logger = AuditLogger(logger)
    audit_logger.log_action(
        user_id="user123",
        action="search",
        resource_type="regulation",
        resource_id="ei-act-s7",
        query="employment insurance eligibility"
    )
