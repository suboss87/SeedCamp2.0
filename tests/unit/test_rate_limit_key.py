"""Rate limit key function tests."""

from unittest.mock import MagicMock, patch


def test_get_client_ip_ignores_forwarded_by_default():
    """X-Forwarded-For is ignored by default to prevent spoofed rate-limit keys."""
    from app.main import _get_client_ip

    request = MagicMock()
    request.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18, 150.172.238.178"}
    request.client = MagicMock()
    request.client.host = "192.168.1.100"
    result = _get_client_ip(request)
    assert result == "192.168.1.100"


def test_get_client_ip_behind_proxy_uses_x_real_ip():
    """With RATE_LIMIT_BEHIND_PROXY=true, the proxy-set X-Real-IP is used."""
    from app.main import _get_client_ip, settings

    request = MagicMock()
    request.headers = {"X-Real-IP": "203.0.113.50"}
    request.client = MagicMock()
    request.client.host = "10.0.0.1"
    with patch.object(settings, "rate_limit_behind_proxy", True):
        result = _get_client_ip(request)
    assert result == "203.0.113.50"


def test_get_client_ip_behind_proxy_falls_back_without_header():
    """Behind a proxy but missing X-Real-IP, falls back to direct IP."""
    from app.main import _get_client_ip, settings

    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "10.0.0.1"
    with patch.object(settings, "rate_limit_behind_proxy", True):
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
