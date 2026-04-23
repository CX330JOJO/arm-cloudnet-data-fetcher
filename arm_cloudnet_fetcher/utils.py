"""Utility functions for data fetching and processing."""

import logging
import sys
import time
from functools import wraps
from typing import Callable, Any

import requests


def setup_logging(level: str = "INFO", log_format: str = None) -> logging.Logger:
    """Configure root logger with specified level and format."""
    logger = logging.getLogger("arm_cloudnet_fetcher")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    return logger


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    """Decorator to retry a function on exception."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, ConnectionError) as exc:
                    if attempt == max_retries:
                        raise
                    time.sleep(delay * attempt)
        return wrapper
    return decorator


def validate_date_range(start_date: str, end_date: str) -> tuple:
    """Validate and normalize date strings (YYYY-MM-DD)."""
    from datetime import datetime
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    if start > end:
        raise ValueError("start_date must not be later than end_date")
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
