"""
Metrics Collection Module

Provides metrics collection and monitoring capabilities for:
- Counter metrics (requests, errors, etc.)
- Gauge metrics (active connections, queue size, etc.)
- Histogram metrics (latency, duration, etc.)
- Custom metrics

Standard Practices:
- Prometheus-compatible metrics
- In-memory aggregation
- Periodic flushing
- Thread-safe operations
"""

import time
from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional, Any
import logging


logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Thread-safe metrics collector for application monitoring.

    Collects various types of metrics and provides methods to
    query and export them. Follows Prometheus naming conventions.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MetricsCollector, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize metrics collector."""
        if self._initialized:
            return

        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, float] = {}
        self._metadata: Dict[str, Any] = {}
        self._lock = Lock()
        self._initialized = True

    def increment(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.

        Args:
            metric_name: Name of the metric
            value: Value to increment by (default: 1)
            labels: Optional labels for the metric

        Example:
            >>> metrics.increment("requests_total")
            >>> metrics.increment("errors_total", labels={"type": "validation"})
        """
        with self._lock:
            full_name = self._build_metric_name(metric_name, labels)
            self._counters[full_name] += value
            logger.debug(f"Counter incremented: {full_name} (+{value})")

    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric to a specific value.

        Args:
            metric_name: Name of the metric
            value: Value to set
            labels: Optional labels for the metric

        Example:
            >>> metrics.set_gauge("active_connections", 42)
            >>> metrics.set_gauge("memory_usage_bytes", 1024000)
        """
        with self._lock:
            full_name = self._build_metric_name(metric_name, labels)
            self._gauges[full_name] = value
            logger.debug(f"Gauge set: {full_name} = {value}")

    def observe(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram observation.

        Args:
            metric_name: Name of the metric
            value: Value to observe
            labels: Optional labels for the metric

        Example:
            >>> metrics.observe("request_duration_seconds", 0.152)
            >>> metrics.observe("document_size_bytes", 1024)
        """
        with self._lock:
            full_name = self._build_metric_name(metric_name, labels)
            self._histograms[full_name].append(value)
            logger.debug(f"Histogram observation: {full_name} = {value}")

    def start_timer(self, timer_name: str) -> None:
        """
        Start a timer for measuring duration.

        Args:
            timer_name: Name of the timer

        Example:
            >>> metrics.start_timer("document_processing")
            >>> # ... do work ...
            >>> metrics.stop_timer("document_processing")
        """
        with self._lock:
            self._timers[timer_name] = time.time()
            logger.debug(f"Timer started: {timer_name}")

    def stop_timer(self, timer_name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """
        Stop a timer and record the duration.

        Args:
            timer_name: Name of the timer
            labels: Optional labels for the metric

        Returns:
            Duration in seconds, or None if timer not found

        Example:
            >>> metrics.start_timer("document_processing")
            >>> # ... do work ...
            >>> duration = metrics.stop_timer("document_processing")
        """
        with self._lock:
            if timer_name not in self._timers:
                logger.warning(f"Timer not found: {timer_name}")
                return None

            start_time = self._timers.pop(timer_name)
            duration = time.time() - start_time

            # Record as histogram observation
            metric_name = f"{timer_name}_duration_seconds"
            full_name = self._build_metric_name(metric_name, labels)
            self._histograms[full_name].append(duration)

            logger.debug(f"Timer stopped: {timer_name} ({duration:.3f}s)")
            return duration

    def get_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current value of a counter metric."""
        with self._lock:
            full_name = self._build_metric_name(metric_name, labels)
            return self._counters.get(full_name, 0)

    def get_gauge(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current value of a gauge metric."""
        with self._lock:
            full_name = self._build_metric_name(metric_name, labels)
            return self._gauges.get(full_name)

    def get_histogram_stats(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Dict[str, float]]:
        """
        Get statistics for a histogram metric.

        Returns:
            Dictionary with min, max, mean, median, p95, p99 values
        """
        with self._lock:
            full_name = self._build_metric_name(metric_name, labels)
            values = self._histograms.get(full_name)

            if not values:
                return None

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": sum(sorted_values) / count,
                "median": sorted_values[count // 2],
                "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
                "p99": sorted_values[int(count * 0.99)] if count > 0 else 0,
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in a structured format.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name.split("{")[0])
                    for name in self._histograms.keys()
                },
                "metadata": self._metadata,
            }
            return metrics_data

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            logger.info("All metrics reset")

    def flush(self) -> Dict[str, Any]:
        """
        Flush metrics to external system (e.g., Prometheus, CloudWatch).

        This is where you would implement integration with your
        monitoring system.

        Returns:
            Current metrics snapshot
        """
        metrics_data = self.get_all_metrics()
        logger.info(f"Metrics flushed: {len(metrics_data['counters'])} counters, "
                   f"{len(metrics_data['gauges'])} gauges, "
                   f"{len(metrics_data['histograms'])} histograms")
        return metrics_data

    def _build_metric_name(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Build full metric name with labels."""
        if not labels:
            return metric_name

        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{metric_name}{{{label_str}}}"

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata information (version, hostname, etc.)."""
        with self._lock:
            self._metadata[key] = value


class timer:
    """
    Context manager and decorator for timing operations.

    Usage as context manager:
        >>> with timer("my_operation"):
        ...     # Your code here
        ...     pass

    Usage as decorator:
        >>> @timer("my_function")
        ... def my_function():
        ...     pass
    """

    def __init__(self, name: str, metrics_collector: Optional[MetricsCollector] = None):
        """Initialize timer."""
        self.name = name
        self.metrics = metrics_collector or MetricsCollector()

    def __enter__(self):
        """Start timer."""
        self.metrics.start_timer(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer."""
        self.metrics.stop_timer(self.name)

    def __call__(self, func):
        """Decorator implementation."""
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper
