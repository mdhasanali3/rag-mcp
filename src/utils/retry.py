"""
Retry Handler

Implements retry logic with exponential backoff.

Standard Practices:
- Exponential backoff
- Jitter for distributed systems
- Configurable retry conditions
- Exception handling
"""

import asyncio
import random
from typing import Callable, Optional, Type, Tuple
from functools import wraps


class RetryHandler:
    """Handler for retrying operations with exponential backoff."""

    @staticmethod
    async def retry_async(
        func: Callable,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Retry an async function with exponential backoff.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            backoff_factor: Backoff multiplier
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Add random jitter to delay
            exceptions: Tuple of exceptions to catch

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func()
            except exceptions as e:
                last_exception = e

                if attempt == max_retries:
                    raise

                # Calculate next delay
                if jitter:
                    delay = min(delay * backoff_factor, max_delay) * (0.5 + random.random())
                else:
                    delay = min(delay * backoff_factor, max_delay)

                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        raise last_exception

    @staticmethod
    def retry_decorator(
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Decorator for retrying functions.

        Usage:
            @RetryHandler.retry_decorator(max_retries=3)
            async def my_function():
                pass
        """

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async def attempt():
                    return await func(*args, **kwargs)

                return await RetryHandler.retry_async(
                    attempt,
                    max_retries=max_retries,
                    backoff_factor=backoff_factor,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    jitter=jitter,
                    exceptions=exceptions
                )

            return wrapper

        return decorator
