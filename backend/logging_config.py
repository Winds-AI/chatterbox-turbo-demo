import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_gpu_stats():
    """Get current GPU memory and utilization stats.

    Returns:
        dict with keys: memory_used_mb, memory_total_mb, memory_percent, utilization_percent
        or None if CUDA is not available
    """
    import torch

    if not torch.cuda.is_available():
        return None

    try:
        device = torch.cuda.current_device()
        mem_used = torch.cuda.memory_allocated(device) / (1024**2)
        mem_total = torch.cuda.get_device_properties(device).total_memory / (1024**2)
        mem_percent = (mem_used / mem_total) * 100

        try:
            util = torch.cuda.utilization(device)
        except Exception:
            util = 0

        return {
            "memory_used_mb": round(mem_used, 2),
            "memory_total_mb": round(mem_total, 2),
            "memory_percent": round(mem_percent, 2),
            "utilization_percent": util,
        }
    except Exception:
        return None


def log_request_start(logger, endpoint: str, details: str):
    """Log the start of a request."""
    logger.info(f"[{endpoint}] Request started: {details}")


from typing import Optional


def log_request_end(
    logger, endpoint: str, elapsed: float, gpu_stats: Optional[dict] = None
):
    """Log the end of a successful request."""
    if gpu_stats:
        logger.info(
            f"[{endpoint}] SUCCESS in {elapsed:.2f}s. "
            f"GPU: {gpu_stats['memory_used_mb']:.0f}MB ({gpu_stats['memory_percent']:.0f}%), "
            f"Util: {gpu_stats['utilization_percent']}%"
        )
    else:
        logger.info(f"[{endpoint}] SUCCESS in {elapsed:.2f}s. GPU: N/A (CPU mode)")


def log_request_error(logger, endpoint: str, elapsed: float, error: str):
    """Log a failed request."""
    logger.error(f"[{endpoint}] FAILED in {elapsed:.2f}s: {error}")
