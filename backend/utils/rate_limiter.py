"""
Rate Limiting Utilities

Comprehensive rate limiting implementation for API protection:
- Token bucket algorithm
- Per-user and per-IP rate limits
- Endpoint-specific limits
- Distributed rate limiting with Redis
- In-memory fallback
- Rate limit headers

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import logging
import hashlib

logger = logging.getLogger(__name__)


# === Rate Limit Configuration ===

@dataclass
class RateLimitRule:
    """Configuration for a rate limit rule"""
    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    key_prefix: str = "ratelimit"  # Redis key prefix

    @property
    def window_name(self) -> str:
        """Human-readable window description"""
        if self.window_seconds < 60:
            return f"{self.window_seconds}s"
        elif self.window_seconds < 3600:
            return f"{self.window_seconds // 60}m"
        else:
            return f"{self.window_seconds // 3600}h"

    def __str__(self) -> str:
        return f"{self.requests} requests per {self.window_name}"


# === Token Bucket Rate Limiter ===

class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate

        # Update bucket
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed successfully, False if insufficient
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False

    def peek(self) -> float:
        """Get current token count without consuming"""
        with self._lock:
            self._refill()
            return self.tokens


# === In-Memory Rate Limiter ===

@dataclass
class RateLimitEntry:
    """Entry in rate limit tracking"""
    count: int = 0
    window_start: float = field(default_factory=time.time)
    reset_at: float = field(default_factory=time.time)


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window"""

    def __init__(self):
        self.limits: Dict[str, RateLimitEntry] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # Cleanup every 5 minutes
        self._last_cleanup = time.time()

    def _cleanup_expired(self):
        """Remove expired entries"""
        now = time.time()

        if now - self._last_cleanup < self._cleanup_interval:
            return

        expired_keys = [
            key for key, entry in self.limits.items()
            if entry.reset_at < now
        ]

        for key in expired_keys:
            del self.limits[key]

        self._last_cleanup = now
        logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries")

    def check_limit(
        self,
        key: str,
        rule: RateLimitRule
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limit

        Args:
            key: Unique identifier (user_id, IP, etc.)
            rule: Rate limit rule to apply

        Returns:
            Tuple of (allowed, info_dict)
        """
        with self._lock:
            self._cleanup_expired()

            now = time.time()
            full_key = f"{rule.key_prefix}:{key}"

            # Get or create entry
            if full_key not in self.limits:
                self.limits[full_key] = RateLimitEntry(
                    count=0,
                    window_start=now,
                    reset_at=now + rule.window_seconds
                )

            entry = self.limits[full_key]

            # Check if window has expired
            if now >= entry.reset_at:
                # Reset window
                entry.count = 0
                entry.window_start = now
                entry.reset_at = now + rule.window_seconds

            # Check limit
            if entry.count < rule.requests:
                entry.count += 1
                allowed = True
            else:
                allowed = False

            # Calculate info
            remaining = max(0, rule.requests - entry.count)
            retry_after = int(entry.reset_at - now) if not allowed else 0

            info = {
                'allowed': allowed,
                'limit': rule.requests,
                'remaining': remaining,
                'reset_at': entry.reset_at,
                'retry_after': retry_after
            }

            return allowed, info


# === Redis Rate Limiter ===

class RedisRateLimiter:
    """Redis-based distributed rate limiter"""

    def __init__(self, redis_client=None):
        """
        Initialize Redis rate limiter

        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis = redis_client
        self.available = False

        if redis_client:
            try:
                redis_client.ping()
                self.available = True
                logger.info("Redis rate limiter initialized")
            except Exception as e:
                logger.warning(f"Redis unavailable, rate limiter disabled: {e}")

    def check_limit(
        self,
        key: str,
        rule: RateLimitRule
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check rate limit using Redis

        Args:
            key: Unique identifier
            rule: Rate limit rule

        Returns:
            Tuple of (allowed, info_dict)
        """
        if not self.available:
            # Redis unavailable, allow all requests
            return True, {
                'allowed': True,
                'limit': rule.requests,
                'remaining': rule.requests,
                'retry_after': 0
            }

        try:
            now = time.time()
            redis_key = f"{rule.key_prefix}:{key}"

            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Get current count
            pipe.get(redis_key)
            pipe.ttl(redis_key)

            results = pipe.execute()
            current_count = int(results[0]) if results[0] else 0
            ttl = results[1]

            # Check limit
            if current_count < rule.requests:
                # Increment counter
                pipe = self.redis.pipeline()
                pipe.incr(redis_key)

                # Set expiry if new key
                if ttl < 0:
                    pipe.expire(redis_key, rule.window_seconds)

                pipe.execute()

                allowed = True
                remaining = rule.requests - current_count - 1
                retry_after = 0
            else:
                allowed = False
                remaining = 0
                retry_after = ttl if ttl > 0 else rule.window_seconds

            info = {
                'allowed': allowed,
                'limit': rule.requests,
                'remaining': remaining,
                'retry_after': retry_after,
                'reset_at': now + (ttl if ttl > 0 else rule.window_seconds)
            }

            return allowed, info

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # On error, allow request (fail open)
            return True, {
                'allowed': True,
                'limit': rule.requests,
                'remaining': rule.requests,
                'retry_after': 0
            }


# === Multi-Tier Rate Limiter ===

class MultiTierRateLimiter:
    """
    Multi-tier rate limiter with fallback

    Tries Redis first, falls back to in-memory
    """

    def __init__(self, redis_client=None):
        """
        Initialize multi-tier rate limiter

        Args:
            redis_client: Optional Redis client for distributed limiting
        """
        self.redis_limiter = RedisRateLimiter(redis_client) if redis_client else None
        self.memory_limiter = InMemoryRateLimiter()

        logger.info(
            f"Multi-tier rate limiter initialized "
            f"(Redis: {self.redis_limiter.available if self.redis_limiter else False})"
        )

    def check_limit(
        self,
        key: str,
        rule: RateLimitRule
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check rate limit (tries Redis, falls back to memory)

        Args:
            key: Unique identifier
            rule: Rate limit rule

        Returns:
            Tuple of (allowed, info_dict)
        """
        # Try Redis first if available
        if self.redis_limiter and self.redis_limiter.available:
            return self.redis_limiter.check_limit(key, rule)

        # Fall back to in-memory
        return self.memory_limiter.check_limit(key, rule)


# === Rate Limit Manager ===

class RateLimitManager:
    """
    Centralized rate limit management

    Manages multiple rate limit rules for different endpoints
    """

    # Default rate limits
    DEFAULT_LIMITS = {
        'global': RateLimitRule(requests=100, window_seconds=60),  # 100/min
        'search': RateLimitRule(requests=30, window_seconds=60),  # 30/min
        'rag': RateLimitRule(requests=10, window_seconds=60),  # 10/min (expensive)
        'documents': RateLimitRule(requests=50, window_seconds=60),  # 50/min
        'batch': RateLimitRule(requests=5, window_seconds=60),  # 5/min (expensive)
    }

    def __init__(self, redis_client=None):
        """
        Initialize rate limit manager

        Args:
            redis_client: Optional Redis client
        """
        self.limiter = MultiTierRateLimiter(redis_client)
        self.rules = self.DEFAULT_LIMITS.copy()

    def add_rule(self, name: str, rule: RateLimitRule):
        """Add or update a rate limit rule"""
        self.rules[name] = rule
        logger.info(f"Added rate limit rule '{name}': {rule}")

    def check(
        self,
        identifier: str,
        endpoint: str = 'global'
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check rate limit for an identifier and endpoint

        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            endpoint: Endpoint name (uses 'global' if not found)

        Returns:
            Tuple of (allowed, info_dict)
        """
        # Get rule (default to global)
        rule = self.rules.get(endpoint, self.rules['global'])

        # Create unique key
        key = self._create_key(identifier, endpoint)

        # Check limit
        return self.limiter.check_limit(key, rule)

    def _create_key(self, identifier: str, endpoint: str) -> str:
        """Create unique key for identifier and endpoint"""
        # Hash long identifiers
        if len(identifier) > 50:
            identifier = hashlib.md5(identifier.encode()).hexdigest()

        return f"{endpoint}:{identifier}"

    def get_limit_info(self, endpoint: str = 'global') -> RateLimitRule:
        """Get rate limit rule for endpoint"""
        return self.rules.get(endpoint, self.rules['global'])


# === Global Rate Limiter Instance ===

_rate_limiter: Optional[RateLimitManager] = None


def get_rate_limiter(redis_client=None) -> RateLimitManager:
    """Get or create global rate limiter instance"""
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimitManager(redis_client)

    return _rate_limiter


# === Example Usage ===

if __name__ == "__main__":
    # Example 1: In-memory rate limiter
    limiter = RateLimitManager()

    # Simulate requests
    client_ip = "192.168.1.1"

    for i in range(150):
        allowed, info = limiter.check(client_ip, endpoint='global')

        if not allowed:
            print(f"Request {i + 1}: BLOCKED (retry after {info['retry_after']}s)")
        else:
            print(f"Request {i + 1}: Allowed (remaining: {info['remaining']})")

        time.sleep(0.1)

    # Example 2: Custom rule
    custom_rule = RateLimitRule(requests=5, window_seconds=10)
    limiter.add_rule('custom', custom_rule)

    print(f"\nCustom rule: {custom_rule}")

    # Example 3: Token bucket
    bucket = TokenBucket(capacity=10, refill_rate=1.0)  # 1 token/second

    for i in range(15):
        if bucket.consume():
            print(f"Token {i + 1}: Consumed (remaining: {bucket.peek():.2f})")
        else:
            print(f"Token {i + 1}: REJECTED (available: {bucket.peek():.2f})")

        time.sleep(0.5)
