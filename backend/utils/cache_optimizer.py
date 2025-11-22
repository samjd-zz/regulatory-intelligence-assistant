"""
Advanced Caching Strategies

Intelligent multi-tier caching system with:
- Cache-aside pattern with automatic fallback
- Write-through caching for critical data
- Sliding TTL with access-based refresh
- Cache stampede prevention
- LRU/LFU eviction policies
- Cache warming and preloading
- Cache invalidation strategies

Based on 2025 best practices from Redis documentation.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import time
import hashlib
import threading
from typing import Any, Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import logging
import json

logger = logging.getLogger(__name__)


# === Cache Entry ===

@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: Optional[int]
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds"""
        return time.time() - self.created_at

    @property
    def idle_seconds(self) -> float:
        """Get idle time since last access"""
        return time.time() - self.last_accessed

    def touch(self):
        """Update last access time and increment counter"""
        self.last_accessed = time.time()
        self.access_count += 1


# === Eviction Policies ===

class EvictionPolicy:
    """Base class for cache eviction policies"""

    def select_victim(self, entries: Dict[str, CacheEntry]) -> Optional[str]:
        """Select which entry to evict"""
        raise NotImplementedError


class LRUEviction(EvictionPolicy):
    """Least Recently Used eviction"""

    def select_victim(self, entries: Dict[str, CacheEntry]) -> Optional[str]:
        if not entries:
            return None

        # Find least recently accessed
        victim_key = min(entries.keys(), key=lambda k: entries[k].last_accessed)
        return victim_key


class LFUEviction(EvictionPolicy):
    """Least Frequently Used eviction"""

    def select_victim(self, entries: Dict[str, CacheEntry]) -> Optional[str]:
        if not entries:
            return None

        # Find least frequently accessed
        victim_key = min(entries.keys(), key=lambda k: entries[k].access_count)
        return victim_key


class TTLEviction(EvictionPolicy):
    """Time-To-Live based eviction (oldest first)"""

    def select_victim(self, entries: Dict[str, CacheEntry]) -> Optional[str]:
        if not entries:
            return None

        # Find oldest entry
        victim_key = min(entries.keys(), key=lambda k: entries[k].created_at)
        return victim_key


# === In-Memory Cache ===

class InMemoryCache:
    """
    Advanced in-memory cache with configurable eviction

    Features:
    - LRU/LFU/TTL eviction policies
    - Sliding TTL (refresh on access)
    - Memory limits with automatic eviction
    - Cache statistics and monitoring
    - Thread-safe operations
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[int] = 3600,
        eviction_policy: str = "lru",
        sliding_ttl: bool = False,
        max_memory_mb: Optional[int] = None
    ):
        """
        Initialize cache

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (None = no expiry)
            eviction_policy: "lru", "lfu", or "ttl"
            sliding_ttl: Refresh TTL on access
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.sliding_ttl = sliding_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024 if max_memory_mb else None

        # Select eviction policy
        if eviction_policy == "lru":
            self.eviction_policy = LRUEviction()
        elif eviction_policy == "lfu":
            self.eviction_policy = LFUEviction()
        elif eviction_policy == "ttl":
            self.eviction_policy = TTLEviction()
        else:
            raise ValueError(f"Unknown eviction policy: {eviction_policy}")

        self.cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_memory_bytes = 0

        logger.info(
            f"Initialized cache: max_size={max_size}, ttl={default_ttl}s, "
            f"policy={eviction_policy}, sliding={sliding_ttl}"
        )

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, (list, dict)):
                return len(json.dumps(value).encode('utf-8'))
            else:
                # Rough estimate
                return 100
        except:
            return 100

    def _evict_if_needed(self):
        """Evict entries if cache is full or over memory limit"""
        # Check size limit
        while len(self.cache) >= self.max_size:
            victim_key = self.eviction_policy.select_victim(self.cache)
            if victim_key:
                self._remove_entry(victim_key)
                self.evictions += 1
            else:
                break

        # Check memory limit
        if self.max_memory_bytes:
            while self.total_memory_bytes > self.max_memory_bytes:
                victim_key = self.eviction_policy.select_victim(self.cache)
                if victim_key:
                    self._remove_entry(victim_key)
                    self.evictions += 1
                else:
                    break

    def _remove_entry(self, key: str):
        """Remove entry and update stats"""
        if key in self.cache:
            entry = self.cache[key]
            self.total_memory_bytes -= entry.size_bytes
            del self.cache[key]

    def _cleanup_expired(self):
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            self._remove_entry(key)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            # Periodic cleanup
            if len(self.cache) > 0 and (self.hits + self.misses) % 100 == 0:
                self._cleanup_expired()

            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]

            # Check expiry
            if entry.is_expired:
                self._remove_entry(key)
                self.misses += 1
                return None

            # Update access stats
            entry.touch()

            # Sliding TTL: refresh expiry on access
            if self.sliding_ttl and entry.ttl_seconds:
                entry.created_at = time.time()

            self.hits += 1
            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None = use default)
        """
        with self._lock:
            # Remove old entry if exists
            if key in self.cache:
                self._remove_entry(key)

            # Evict if needed
            self._evict_if_needed()

            # Create new entry
            size = self._estimate_size(value)
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=0,
                ttl_seconds=ttl if ttl is not None else self.default_ttl,
                size_bytes=size
            )

            self.cache[key] = entry
            self.total_memory_bytes += size

    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self._lock:
            if key in self.cache:
                self._remove_entry(key)
                return True
            return False

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.total_memory_bytes = 0
            logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': round(hit_rate, 2),
                'evictions': self.evictions,
                'total_memory_bytes': self.total_memory_bytes,
                'total_memory_mb': round(self.total_memory_bytes / 1024 / 1024, 2)
            }


# === Multi-Tier Cache ===

class MultiTierCache:
    """
    Multi-tier cache with local (in-memory) and remote (Redis) layers

    Implements cache-aside pattern with automatic fallback
    """

    def __init__(
        self,
        local_cache: Optional[InMemoryCache] = None,
        redis_client = None,
        local_ttl: int = 300,  # 5 minutes
        redis_ttl: int = 3600  # 1 hour
    ):
        """
        Initialize multi-tier cache

        Args:
            local_cache: Local in-memory cache (created if not provided)
            redis_client: Redis client instance
            local_ttl: TTL for local cache
            redis_ttl: TTL for Redis cache
        """
        self.local = local_cache or InMemoryCache(
            max_size=1000,
            default_ttl=local_ttl,
            eviction_policy="lru"
        )

        self.redis = redis_client
        self.redis_ttl = redis_ttl
        self.redis_available = False

        if redis_client:
            try:
                redis_client.ping()
                self.redis_available = True
                logger.info("Multi-tier cache: Redis available")
            except:
                logger.warning("Multi-tier cache: Redis unavailable, using local only")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks local, then Redis)

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        # Try local cache first
        value = self.local.get(key)
        if value is not None:
            return value

        # Try Redis if available
        if self.redis_available:
            try:
                redis_value = self.redis.get(key)
                if redis_value:
                    # Deserialize
                    value = json.loads(redis_value)

                    # Populate local cache
                    self.local.set(key, value)

                    return value
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in both cache tiers

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None = use defaults)
        """
        # Set in local cache
        self.local.set(key, value, ttl=ttl)

        # Set in Redis if available
        if self.redis_available:
            try:
                redis_ttl = ttl if ttl else self.redis_ttl
                serialized = json.dumps(value)
                self.redis.setex(key, redis_ttl, serialized)
            except Exception as e:
                logger.error(f"Redis set error: {e}")

    def delete(self, key: str):
        """Delete from both cache tiers"""
        self.local.delete(key)

        if self.redis_available:
            try:
                self.redis.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from both tiers"""
        stats = {
            'local': self.local.get_stats(),
            'redis_available': self.redis_available
        }

        if self.redis_available:
            try:
                redis_info = self.redis.info('stats')
                stats['redis'] = {
                    'keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'keyspace_misses': redis_info.get('keyspace_misses', 0)
                }
            except:
                pass

        return stats


# === Cache Stampede Prevention ===

class StampedeProtectedCache:
    """
    Cache with stampede prevention

    Ensures only one thread computes value on cache miss
    """

    def __init__(self, cache: InMemoryCache):
        self.cache = cache
        self._locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()

    def _get_lock(self, key: str) -> threading.Lock:
        """Get or create lock for key"""
        with self._locks_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute if missing

        Only one thread will compute on cache miss (stampede prevention)

        Args:
            key: Cache key
            compute_func: Function to compute value on miss
            ttl: TTL for cached value

        Returns:
            Cached or computed value
        """
        # Try cache first
        value = self.cache.get(key)
        if value is not None:
            return value

        # Acquire lock for this key
        lock = self._get_lock(key)

        with lock:
            # Double-check after acquiring lock
            value = self.cache.get(key)
            if value is not None:
                return value

            # Compute value
            value = compute_func()

            # Cache result
            self.cache.set(key, value, ttl=ttl)

            return value


# === Cache Warming ===

def warm_cache(
    cache: InMemoryCache,
    data_loader: Callable[[], List[Tuple[str, Any]]],
    batch_size: int = 100
):
    """
    Pre-populate cache with frequently accessed data

    Args:
        cache: Cache to warm
        data_loader: Function that returns list of (key, value) tuples
        batch_size: Number of items to load at once
    """
    logger.info("Starting cache warming...")

    try:
        data = data_loader()

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            for key, value in batch:
                cache.set(key, value)

        logger.info(f"Cache warmed with {len(data)} entries")

    except Exception as e:
        logger.error(f"Cache warming failed: {e}")


# === Example Usage ===

if __name__ == "__main__":
    # Example 1: Basic in-memory cache with LRU
    cache = InMemoryCache(
        max_size=100,
        default_ttl=300,
        eviction_policy="lru",
        sliding_ttl=True
    )

    cache.set("key1", "value1")
    cache.set("key2", {"data": "complex"})

    print(cache.get("key1"))  # "value1"
    print(cache.get_stats())

    # Example 2: Stampede-protected cache
    protected_cache = StampedeProtectedCache(cache)

    def expensive_computation():
        time.sleep(1)
        return "computed_value"

    value = protected_cache.get_or_compute("expensive", expensive_computation)
    print(f"Computed: {value}")

    # Example 3: Multi-tier cache
    # multi_cache = MultiTierCache(redis_client=redis.Redis())
    # multi_cache.set("user:123", {"name": "John"})
    # user = multi_cache.get("user:123")

    print("Cache optimization examples complete!")
