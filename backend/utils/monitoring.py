"""
Monitoring and Observability Utilities

Provides metrics collection, health checks, and observability
hooks for the Regulatory Intelligence Assistant.

Features:
- Service health checks
- Metrics collection (counters, gauges, histograms)
- Performance tracking
- Resource utilization monitoring
- Integration with monitoring systems (Prometheus-compatible)

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import time
import psutil
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading


# === Metrics Collection ===

@dataclass
class Metric:
    """Base metric class"""
    name: str
    help_text: str
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Counter(Metric):
    """Counter metric (monotonically increasing)"""
    value: float = 0.0

    def inc(self, amount: float = 1.0):
        """Increment counter"""
        self.value += amount
        self.timestamp = datetime.now()


@dataclass
class Gauge(Metric):
    """Gauge metric (can go up or down)"""
    value: float = 0.0

    def set(self, value: float):
        """Set gauge value"""
        self.value = value
        self.timestamp = datetime.now()

    def inc(self, amount: float = 1.0):
        """Increment gauge"""
        self.value += amount
        self.timestamp = datetime.now()

    def dec(self, amount: float = 1.0):
        """Decrement gauge"""
        self.value -= amount
        self.timestamp = datetime.now()


@dataclass
class Histogram(Metric):
    """Histogram metric (distribution of values)"""
    observations: List[float] = field(default_factory=list)
    buckets: List[float] = field(default_factory=lambda: [0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0])

    def observe(self, value: float):
        """Record an observation"""
        self.observations.append(value)
        self.timestamp = datetime.now()

        # Keep only recent observations (last 1000)
        if len(self.observations) > 1000:
            self.observations = self.observations[-1000:]

    def get_stats(self) -> Dict[str, float]:
        """Get histogram statistics"""
        if not self.observations:
            return {}

        sorted_obs = sorted(self.observations)
        count = len(sorted_obs)

        return {
            'count': count,
            'sum': sum(sorted_obs),
            'min': sorted_obs[0],
            'max': sorted_obs[-1],
            'mean': sum(sorted_obs) / count,
            'p50': sorted_obs[int(0.50 * count)],
            'p95': sorted_obs[int(0.95 * count)],
            'p99': sorted_obs[int(0.99 * count)]
        }


class MetricsRegistry:
    """Registry for all metrics"""

    def __init__(self):
        """Initialize metrics registry"""
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()

    def register_counter(self, name: str, help_text: str, labels: Optional[Dict] = None) -> Counter:
        """Register a counter metric"""
        with self._lock:
            key = f"counter_{name}"
            if key not in self._metrics:
                self._metrics[key] = Counter(name=name, help_text=help_text, labels=labels or {})
            return self._metrics[key]

    def register_gauge(self, name: str, help_text: str, labels: Optional[Dict] = None) -> Gauge:
        """Register a gauge metric"""
        with self._lock:
            key = f"gauge_{name}"
            if key not in self._metrics:
                self._metrics[key] = Gauge(name=name, help_text=help_text, labels=labels or {})
            return self._metrics[key]

    def register_histogram(self, name: str, help_text: str, labels: Optional[Dict] = None) -> Histogram:
        """Register a histogram metric"""
        with self._lock:
            key = f"histogram_{name}"
            if key not in self._metrics:
                self._metrics[key] = Histogram(name=name, help_text=help_text, labels=labels or {})
            return self._metrics[key]

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all registered metrics"""
        with self._lock:
            return dict(self._metrics)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format"""
        lines = []

        for key, metric in self._metrics.items():
            # HELP line
            lines.append(f"# HELP {metric.name} {metric.help_text}")

            # TYPE line
            metric_type = type(metric).__name__.lower()
            lines.append(f"# TYPE {metric.name} {metric_type}")

            # Metric value(s)
            if isinstance(metric, (Counter, Gauge)):
                label_str = ','.join(f'{k}="{v}"' for k, v in metric.labels.items())
                if label_str:
                    lines.append(f"{metric.name}{{{label_str}}} {metric.value}")
                else:
                    lines.append(f"{metric.name} {metric.value}")

            elif isinstance(metric, Histogram):
                stats = metric.get_stats()
                for stat_name, stat_value in stats.items():
                    lines.append(f"{metric.name}_{stat_name} {stat_value}")

        return '\n'.join(lines)


# Global metrics registry
metrics_registry = MetricsRegistry()


# === Service Health Checks ===

@dataclass
class HealthStatus:
    """Health status for a service component"""
    component: str
    status: str  # healthy, degraded, unhealthy
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'component': self.component,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'checked_at': self.checked_at.isoformat()
        }


class HealthChecker:
    """Health checker for all system components"""

    def __init__(self):
        """Initialize health checker"""
        self._checks: Dict[str, Callable] = {}
        self._cache: Dict[str, HealthStatus] = {}
        self._cache_ttl = timedelta(seconds=30)

    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check function

        Args:
            name: Component name
            check_func: Function that returns HealthStatus
        """
        self._checks[name] = check_func

    def check(self, component: str) -> HealthStatus:
        """
        Check health of a specific component

        Args:
            component: Component name

        Returns:
            HealthStatus
        """
        # Check cache
        if component in self._cache:
            cached = self._cache[component]
            if datetime.now() - cached.checked_at < self._cache_ttl:
                return cached

        # Run check
        if component in self._checks:
            try:
                status = self._checks[component]()
                self._cache[component] = status
                return status
            except Exception as e:
                status = HealthStatus(
                    component=component,
                    status='unhealthy',
                    message=f'Health check failed: {str(e)}'
                )
                return status
        else:
            return HealthStatus(
                component=component,
                status='unknown',
                message='No health check registered'
            )

    def check_all(self) -> Dict[str, HealthStatus]:
        """
        Check health of all registered components

        Returns:
            Dict mapping component names to HealthStatus
        """
        results = {}
        for component in self._checks:
            results[component] = self.check(component)
        return results

    def get_overall_status(self) -> str:
        """
        Get overall system health status

        Returns:
            'healthy', 'degraded', or 'unhealthy'
        """
        statuses = self.check_all()

        if any(s.status == 'unhealthy' for s in statuses.values()):
            return 'unhealthy'
        elif any(s.status == 'degraded' for s in statuses.values()):
            return 'degraded'
        else:
            return 'healthy'


# Global health checker
health_checker = HealthChecker()


# === Resource Monitoring ===

class ResourceMonitor:
    """Monitor system resource utilization"""

    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=0.1)

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get memory usage statistics"""
        mem = psutil.virtual_memory()
        return {
            'total_mb': mem.total / (1024 * 1024),
            'available_mb': mem.available / (1024 * 1024),
            'used_mb': mem.used / (1024 * 1024),
            'percent': mem.percent
        }

    @staticmethod
    def get_disk_usage() -> Dict[str, Any]:
        """Get disk usage statistics"""
        disk = psutil.disk_usage('/')
        return {
            'total_gb': disk.total / (1024 ** 3),
            'used_gb': disk.used / (1024 ** 3),
            'free_gb': disk.free / (1024 ** 3),
            'percent': disk.percent
        }

    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """Get current process information"""
        process = psutil.Process()
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / (1024 * 1024),
            'num_threads': process.num_threads(),
            'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
        }

    @classmethod
    def get_all_metrics(cls) -> Dict[str, Any]:
        """Get all resource metrics"""
        return {
            'cpu': cls.get_cpu_usage(),
            'memory': cls.get_memory_usage(),
            'disk': cls.get_disk_usage(),
            'process': cls.get_process_info(),
            'timestamp': datetime.now().isoformat()
        }


# === Performance Tracking ===

class PerformanceTracker:
    """Track performance metrics for operations"""

    def __init__(self):
        """Initialize performance tracker"""
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def record(self, operation: str, duration_ms: float):
        """
        Record operation performance

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            self.operation_times[operation].append(duration_ms)
            self.operation_counts[operation] += 1

            # Keep only recent measurements (last 1000)
            if len(self.operation_times[operation]) > 1000:
                self.operation_times[operation] = self.operation_times[operation][-1000:]

    def get_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """
        Get performance statistics for an operation

        Args:
            operation: Operation name

        Returns:
            Dict with min, max, mean, p95, p99 or None
        """
        with self._lock:
            if operation not in self.operation_times or not self.operation_times[operation]:
                return None

            times = sorted(self.operation_times[operation])
            count = len(times)

            return {
                'count': count,
                'min_ms': times[0],
                'max_ms': times[-1],
                'mean_ms': sum(times) / count,
                'median_ms': times[count // 2],
                'p95_ms': times[int(0.95 * count)],
                'p99_ms': times[int(0.99 * count)]
            }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations"""
        with self._lock:
            return {
                op: self.get_stats(op)
                for op in self.operation_times.keys()
            }


# Global performance tracker
performance_tracker = PerformanceTracker()


# === Decorators for Monitoring ===

def track_performance(operation_name: str):
    """
    Decorator to track function performance

    Args:
        operation_name: Name of the operation

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                performance_tracker.record(operation_name, duration_ms)

        return wrapper
    return decorator


def count_calls(counter_name: str):
    """
    Decorator to count function calls

    Args:
        counter_name: Counter metric name

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        import functools

        # Register counter
        counter = metrics_registry.register_counter(
            counter_name,
            f"Total calls to {func.__name__}"
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            counter.inc()
            return func(*args, **kwargs)

        return wrapper
    return decorator


# === Example Usage ===

if __name__ == "__main__":
    # Example 1: Metrics
    query_counter = metrics_registry.register_counter(
        "nlp_queries_total",
        "Total number of NLP queries processed"
    )
    query_counter.inc()
    query_counter.inc()

    latency_histogram = metrics_registry.register_histogram(
        "search_latency_seconds",
        "Search latency distribution"
    )
    latency_histogram.observe(0.123)
    latency_histogram.observe(0.456)
    latency_histogram.observe(0.789)

    print("Histogram stats:", latency_histogram.get_stats())

    # Example 2: Health checks
    def check_database():
        return HealthStatus(
            component="database",
            status="healthy",
            message="Database connection OK"
        )

    health_checker.register_check("database", check_database)
    db_health = health_checker.check("database")
    print(f"Database health: {db_health.status}")

    # Example 3: Resource monitoring
    resources = ResourceMonitor.get_all_metrics()
    print(f"CPU Usage: {resources['cpu']}%")
    print(f"Memory Usage: {resources['memory']['percent']}%")

    # Example 4: Performance tracking
    @track_performance("test_operation")
    def slow_function():
        time.sleep(0.1)

    slow_function()
    slow_function()
    slow_function()

    stats = performance_tracker.get_stats("test_operation")
    print(f"Test operation stats: {stats}")

    # Example 5: Prometheus export
    print("\nPrometheus format:")
    print(metrics_registry.export_prometheus())
