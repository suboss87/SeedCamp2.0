"""
Retry Utilities for ModelArk API Calls
Implements exponential backoff, rate limit handling, and error recovery.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ModelArkAPIError(Exception):
    """Base exception for ModelArk API errors."""

    def __init__(
        self, message: str, status_code: int = None, response_body: dict = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body or {}


class RateLimitError(ModelArkAPIError):
    """Rate limit exceeded."""

    pass


class QuotaExceededError(ModelArkAPIError):
    """API quota exceeded."""

    pass


class InvalidAPIKeyError(ModelArkAPIError):
    """Invalid or missing API key."""

    pass


def parse_modelark_error(response: httpx.Response) -> ModelArkAPIError:
    """Parse ModelArk API error response into specific exception."""
    status_code = response.status_code

    try:
        body = response.json()
    except Exception:
        body = {"detail": response.text}

    error_msg = body.get("error", {}).get("message") or body.get(
        "detail", "Unknown error"
    )
    error_code = body.get("error", {}).get("code", "")

    # Map ModelArk error codes to exceptions
    if (
        status_code == 401
        or "invalid" in error_code.lower()
        or "unauthorized" in error_code.lower()
    ):
        return InvalidAPIKeyError(f"Invalid API key: {error_msg}", status_code, body)

    if status_code == 429 or "rate_limit" in error_code.lower():
        return RateLimitError(f"Rate limit exceeded: {error_msg}", status_code, body)

    if status_code == 403 and "quota" in error_code.lower():
        return QuotaExceededError(f"Quota exceeded: {error_msg}", status_code, body)

    return ModelArkAPIError(
        f"ModelArk API error ({status_code}): {error_msg}", status_code, body
    )


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retriable_status_codes: tuple = (408, 429, 500, 502, 503, 504),
):
    """
    Decorator for async functions to retry with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay on each retry
        retriable_status_codes: HTTP status codes that should trigger retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code

                    # Parse ModelArk-specific error
                    modelark_error = parse_modelark_error(e.response)

                    # Don't retry on auth errors or quota exceeded
                    if isinstance(
                        modelark_error, (InvalidAPIKeyError, QuotaExceededError)
                    ):
                        logger.error(f"{func.__name__} failed: {modelark_error}")
                        raise modelark_error

                    # Check if retriable
                    if status_code not in retriable_status_codes:
                        logger.error(
                            f"{func.__name__} failed with non-retriable error: {modelark_error}"
                        )
                        raise modelark_error

                    # Rate limit handling with Retry-After header
                    if status_code == 429:
                        retry_after = e.response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = float(retry_after)
                            except ValueError:
                                pass

                    last_exception = modelark_error

                except (
                    httpx.TimeoutException,
                    httpx.NetworkError,
                    httpx.ConnectError,
                ) as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} network error (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )

                # Don't sleep after last attempt
                if attempt < max_retries:
                    logger.info(
                        f"Retrying {func.__name__} in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            # All retries exhausted
            logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
            raise last_exception or Exception(f"{func.__name__} failed")

        return wrapper

    return decorator


async def validate_api_key(api_key: str, base_url: str) -> bool:
    """
    Validate ModelArk API key by making a test request.
    Returns True if valid, raises exception otherwise.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Use chat completions endpoint with minimal tokens to test auth
    test_payload = {
        "model": settings.script_model,
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=test_payload,
            )

            if resp.status_code == 401:
                raise InvalidAPIKeyError("Invalid or missing ModelArk API key")

            if resp.status_code == 403:
                # May be valid but no access to this model - that's fine for validation
                return True

            resp.raise_for_status()
            return True

    except httpx.HTTPStatusError as e:
        error = parse_modelark_error(e.response)
        logger.error(f"API key validation failed: {error}")
        raise error
    except Exception as e:
        logger.error(f"Failed to validate API key: {e}")
        raise ModelArkAPIError(f"API key validation error: {e}")
