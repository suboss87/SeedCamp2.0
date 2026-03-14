"""Request ID middleware tests."""

import pytest


@pytest.fixture
def client():
    """Test client without auth requirement."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_request_id_generated(client):
    """Response includes X-Request-ID when not provided."""
    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) == 12


def test_request_id_passthrough(client):
    """Response echoes client-provided X-Request-ID."""
    resp = client.get("/health", headers={"X-Request-ID": "test-trace-123"})
    assert resp.headers["X-Request-ID"] == "test-trace-123"
