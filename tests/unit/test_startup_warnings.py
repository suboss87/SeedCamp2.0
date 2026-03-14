"""Startup warning tests for production mode."""

from app.config import Settings


def test_production_default_is_false():
    """production flag defaults to False."""
    s = Settings(ark_api_key="test")
    assert s.production is False


def test_production_flag_from_env(monkeypatch):
    """production flag can be set via environment."""
    monkeypatch.setenv("PRODUCTION", "true")
    s = Settings(ark_api_key="test")
    assert s.production is True


def test_memory_backend_is_default():
    """persistence_backend defaults to memory (validates the concern)."""
    s = Settings(ark_api_key="test")
    assert s.persistence_backend == "memory"
