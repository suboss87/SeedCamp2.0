"""Rate limit key function tests."""

from unittest.mock import MagicMock


def test_get_client_ip_forwarded():
    """X-Forwarded-For returns first IP in chain."""
    from app.main import _get_client_ip

    request = MagicMock()
    request.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18, 150.172.238.178"}
    result = _get_client_ip(request)
    assert result == "203.0.113.50"


def test_get_client_ip_single_forwarded():
    """Single X-Forwarded-For IP works."""
    from app.main import _get_client_ip

    request = MagicMock()
    request.headers = {"X-Forwarded-For": "10.0.0.1"}
    result = _get_client_ip(request)
    assert result == "10.0.0.1"


def test_get_client_ip_no_forwarded():
    """Without X-Forwarded-For, falls back to direct IP."""
    from app.main import _get_client_ip

    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "192.168.1.100"
    result = _get_client_ip(request)
    assert result == "192.168.1.100"
