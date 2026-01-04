from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
)
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info
import torch
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class MetricsManager:
    _instance = None
    _registry = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_metrics()
        return cls._instance

    def _initialize_metrics(self):
        self._registry = CollectorRegistry()

        self.request_count = Counter(
            "tts_requests_total",
            "Total number of TTS requests",
            ["endpoint", "status"],
            registry=self._registry,
        )

        self.request_duration = Histogram(
            "tts_request_duration_seconds",
            "TTS request duration in seconds",
            ["endpoint", "operation"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self._registry,
        )

        self.request_duration_phases = Histogram(
            "tts_request_phase_duration_seconds",
            "Duration of specific phases in TTS processing",
            ["phase"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self._registry,
        )

        self.gpu_memory_used = Gauge(
            "tts_gpu_memory_mb",
            "GPU memory usage in MB",
            ["device"],
            registry=self._registry,
        )

        self.gpu_utilization = Gauge(
            "tts_gpu_utilization_percent",
            "GPU SM utilization percentage",
            ["device"],
            registry=self._registry,
        )

        self.voice_cache_size = Gauge(
            "tts_voice_cache_size",
            "Number of cached voice embeddings",
            registry=self._registry,
        )

        self.model_loaded = Gauge(
            "tts_model_loaded",
            "Whether the TTS model is loaded (1 for yes, 0 for no)",
            registry=self._registry,
        )

        self.concurrent_requests = Gauge(
            "tts_concurrent_requests",
            "Number of concurrent requests being processed",
            registry=self._registry,
        )

        self.audio_output_size = Histogram(
            "tts_audio_output_size_bytes",
            "Size of generated audio output in bytes",
            buckets=[1024, 4096, 16384, 65536, 262144, 1048576],
            registry=self._registry,
        )

        self.text_length = Histogram(
            "tts_input_text_length_chars",
            "Length of input text in characters",
            buckets=[10, 50, 100, 250, 500, 1000, 2000],
            registry=self._registry,
        )

    def record_request(self, endpoint: str, status: str = "success"):
        self.request_count.labels(endpoint=endpoint, status=status).inc()

    def record_duration(self, endpoint: str, operation: str, duration: float):
        self.request_duration.labels(endpoint=endpoint, operation=operation).observe(
            duration
        )

    def record_phase_duration(self, phase: str, duration: float):
        self.request_duration_phases.labels(phase=phase).observe(duration)

    def update_gpu_metrics(self):
        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            memory_used = torch.cuda.memory_allocated(device) / (1024 * 1024)
            self.gpu_memory_used.labels(device=str(device)).set(memory_used)

            if hasattr(torch.cuda, "utilization"):
                try:
                    util = torch.cuda.utilization(device)
                    self.gpu_utilization.labels(device=str(device)).set(util)
                except:
                    pass

    def update_voice_cache(self, size: int):
        self.voice_cache_size.set(size)

    def update_model_loaded(self, loaded: bool):
        self.model_loaded.set(1 if loaded else 0)

    def increment_concurrent(self):
        self.concurrent_requests.inc()

    def decrement_concurrent(self):
        self.concurrent_requests.dec()

    def record_audio_output(self, size_bytes: int):
        self.audio_output_size.observe(size_bytes)

    def record_text_length(self, length: int):
        self.text_length.observe(length)

    def get_metrics(self):
        return generate_latest(self._registry)


def track_request_duration(endpoint: str, operation: str = "total"):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = MetricsManager()
            manager.increment_concurrent()
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                manager.record_request(endpoint, status)
                duration = time.time() - start_time
                manager.record_duration(endpoint, operation, duration)
                return result
            except Exception as e:
                status = "error"
                manager.record_request(endpoint, status)
                duration = time.time() - start_time
                manager.record_duration(endpoint, operation, duration)
                raise
            finally:
                manager.decrement_concurrent()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = MetricsManager()
            manager.increment_concurrent()
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                manager.record_request(endpoint, status)
                duration = time.time() - start_time
                manager.record_duration(endpoint, operation, duration)
                return result
            except Exception as e:
                status = "error"
                manager.record_request(endpoint, status)
                duration = time.time() - start_time
                manager.record_duration(endpoint, operation, duration)
                raise
            finally:
                manager.decrement_concurrent()

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_phase(phase: str):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = MetricsManager()
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                manager.record_phase_duration(phase, time.time() - start_time)
                return result
            except Exception:
                manager.record_phase_duration(phase, time.time() - start_time)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = MetricsManager()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                manager.record_phase_duration(phase, time.time() - start_time)
                return result
            except Exception:
                manager.record_phase_duration(phase, time.time() - start_time)
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


metrics_manager = MetricsManager()
