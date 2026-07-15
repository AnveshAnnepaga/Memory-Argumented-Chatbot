# File: app/core/retry.py
import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Type, Union
from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("app.core.retry")


def get_async_retry_policy(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exception_types: Union[Type[Exception], tuple] = Exception,
) -> AsyncRetrying:
    """
    (`6.8 Retry Policy`)
    Returns a configured tenacity AsyncRetrying instance with exponential backoff and logging.
    """
    return AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type(exception_types),
        reraise=True,
    )


def get_sync_retry_policy(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exception_types: Union[Type[Exception], tuple] = Exception,
) -> Retrying:
    """
    (`6.8 Retry Policy`)
    Returns a configured tenacity Retrying instance for synchronous operations.
    """
    return Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type(exception_types),
        reraise=True,
    )


def execute_with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 8.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
):
    """
    Decorator applying exponential backoff retry logic (`6.8 Retry Policy`)
    to both async and sync infrastructure operations.
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                async for attempt in get_async_retry_policy(max_attempts, min_wait, max_wait, exceptions):
                    with attempt:
                        try:
                            return await func(*args, **kwargs)
                        except exceptions as e:
                            logger.warning(
                                f"[Retry Policy] Operation '{func.__name__}' failed (Attempt {attempt.retry_state.attempt_number}/{max_attempts}). Error: {e}"
                            )
                            raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                for attempt in get_sync_retry_policy(max_attempts, min_wait, max_wait, exceptions):
                    with attempt:
                        try:
                            return func(*args, **kwargs)
                        except exceptions as e:
                            logger.warning(
                                f"[Retry Policy] Operation '{func.__name__}' failed (Attempt {attempt.retry_state.attempt_number}/{max_attempts}). Error: {e}"
                            )
                            raise
            return sync_wrapper
    return decorator
