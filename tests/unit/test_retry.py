"""Tests for resilient API integration (Pattern 5).

Verifies: error classification, retry vs no-retry behavior, backoff exhaustion.
Uses httpx.Response mocks — no real network calls.
"""
import pytest
import httpx

from app.utils.retry import (
    parse_modelark_error,
    retry_with_backoff,
    InvalidAPIKeyError,
    QuotaExceededError,
    RateLimitError,
    ModelArkAPIError,
)


# ── Error Classification ──────────────────────────────────────────────────────

class TestParseModelarkError:
    """Verify HTTP responses map to the correct exception type."""

    def _make_response(self, status_code: int, body: dict) -> httpx.Response:
        """Build a fake httpx.Response with a JSON body."""
        import json
        resp = httpx.Response(
            status_code=status_code,
            content=json.dumps(body).encode(),
            headers={"content-type": "application/json"},
            request=httpx.Request("POST", "https://test.example.com"),
        )
        return resp

    def test_401_returns_invalid_api_key(self):
        resp = self._make_response(401, {"error": {"message": "bad key", "code": ""}})
        err = parse_modelark_error(resp)
        assert isinstance(err, InvalidAPIKeyError)

    def test_429_returns_rate_limit(self):
        resp = self._make_response(429, {"error": {"message": "slow down", "code": "rate_limit"}})
        err = parse_modelark_error(resp)
        assert isinstance(err, RateLimitError)

    def test_403_with_quota_returns_quota_exceeded(self):
        resp = self._make_response(403, {"error": {"message": "quota hit", "code": "quota_exceeded"}})
        err = parse_modelark_error(resp)
        assert isinstance(err, QuotaExceededError)

    def test_403_without_quota_returns_generic(self):
        resp = self._make_response(403, {"error": {"message": "forbidden", "code": "forbidden"}})
        err = parse_modelark_error(resp)
        assert isinstance(err, ModelArkAPIError)
        assert not isinstance(err, QuotaExceededError)

    def test_500_returns_generic_error(self):
        resp = self._make_response(500, {"error": {"message": "internal", "code": "server_error"}})
        err = parse_modelark_error(resp)
        assert isinstance(err, ModelArkAPIError)
        assert not isinstance(err, (InvalidAPIKeyError, RateLimitError, QuotaExceededError))


# ── Retry Behavior ────────────────────────────────────────────────────────────

class TestRetryWithBackoff:
    """Verify retry/no-retry logic with fast delays (initial_delay=0.01)."""

    async def test_success_on_first_try(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeed()
        assert result == "ok"
        assert call_count == 1

    async def test_retry_on_network_error_then_succeed(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("connection refused")
            return "recovered"

        result = await flaky()
        assert result == "recovered"
        assert call_count == 3

    async def test_no_retry_on_auth_error(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        async def bad_auth():
            nonlocal call_count
            call_count += 1
            import json
            resp = httpx.Response(
                401,
                content=json.dumps({"error": {"message": "invalid key", "code": ""}}).encode(),
                headers={"content-type": "application/json"},
                request=httpx.Request("POST", "https://test.example.com"),
            )
            raise httpx.HTTPStatusError("401", request=resp.request, response=resp)

        with pytest.raises(InvalidAPIKeyError):
            await bad_auth()
        assert call_count == 1  # no retries

    async def test_no_retry_on_quota_error(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        async def quota_hit():
            nonlocal call_count
            call_count += 1
            import json
            resp = httpx.Response(
                403,
                content=json.dumps({"error": {"message": "quota", "code": "quota_exceeded"}}).encode(),
                headers={"content-type": "application/json"},
                request=httpx.Request("POST", "https://test.example.com"),
            )
            raise httpx.HTTPStatusError("403", request=resp.request, response=resp)

        with pytest.raises(QuotaExceededError):
            await quota_hit()
        assert call_count == 1  # no retries

    async def test_exhausts_retries_raises_last_exception(self):
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("always down")

        with pytest.raises(httpx.ConnectError):
            await always_fails()
        assert call_count == 3  # initial + 2 retries
