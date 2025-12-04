import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger("api")
F = TypeVar("F", bound=Callable[..., Any])


def log_performance(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__qualname__} completed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                f"{func.__qualname__} failed after {elapsed:.2f}ms: {e}")
            raise
    return wrapper  # type: ignore


def log_async_performance(func: F) -> F:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"{func.__qualname__} completed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                f"{func.__qualname__} failed after {elapsed:.2f}ms: {e}")
            raise
    return wrapper  # type: ignore
