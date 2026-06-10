"""Tests for security hardening: CORS config, API key auth, upload limits, rate limiting."""

import sys
from unittest.mock import MagicMock, patch

import pytest

# ── Config-only tests (no app import needed) ────────────────────────────────


class TestCORSConfiguration:
    """Verify CORS origins are read from config."""

    def test_cors_origins_parsed_from_comma_separated(self):
        from app.config import Settings

        s = Settings(ark_api_key="x", cors_origins="https://a.com,https://b.com")
        origins = [o.strip() for o in s.cors_origins.split(",")]
        assert origins == ["https://a.com", "https://b.com"]

    def test_cors_origins_default_is_wildcard(self):
        from app.config import Settings

        s = Settings(ark_api_key="x")
        assert s.cors_origins == "*"


class TestUploadSizeConfig:
    """Verify file upload size configuration."""

    def test_config_default_max_upload_size(self):
        from app.config import Settings

        s = Settings(ark_api_key="x")
        assert s.max_upload_size_mb == 10

    def test_config_custom_max_upload_size(self):
        from app.config import Settings

        s = Settings(ark_api_key="x", max_upload_size_mb=25)
        assert s.max_upload_size_mb == 25


class TestRateLimitConfig:
    """Verify rate limit configuration is read from settings."""

    def test_config_default_rate_limit(self):
        from app.config import Settings

        s = Settings(ark_api_key="x")
        assert s.rate_limit == "60/minute"

    def test_config_custom_rate_limit(self):
        from app.config import Settings

        s = Settings(ark_api_key="x", rate_limit="100/minute")
        assert s.rate_limit == "100/minute"


class TestAPIKeyConfig:
    """Verify API key configuration."""

    def test_api_key_default_empty(self):
        from app.config import Settings

        s = Settings(ark_api_key="x")
        assert s.api_key == ""

    def test_api_key_custom(self):
        from app.config import Settings

        s = Settings(ark_api_key="x", api_key="my-secret")
        assert s.api_key == "my-secret"


# ── Integration tests requiring app import ───────────────────────────────────
# These mock out google.cloud to avoid the cryptography/Firestore import issue.


def _mock_google_cloud():
    """Pre-populate sys.modules with mocks for google.cloud deps."""
    mock_gcs = MagicMock()
    mock_firestore = MagicMock()
    patches = {
        "google.cloud.storage": mock_gcs,
        "google.cloud.firestore": mock_firestore,
        "google.cloud.firestore.AsyncClient": MagicMock(),
    }
    return patches


@pytest.fixture
def _patch_google():
    """Patch google.cloud modules before importing app.main."""
    mocks = _mock_google_cloud()
    saved = {}
    for mod_name, mock_obj in mocks.items():
        saved[mod_name] = sys.modules.get(mod_name)
        sys.modules[mod_name] = mock_obj
    yield
    for mod_name, orig in saved.items():
        if orig is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = orig


@pytest.fixture
def client_no_auth(_patch_google):
    """App client with API_KEY disabled (default)."""
    with patch("app.config.settings.api_key", ""):
        from fastapi.testclient import TestClient

        from app.main import app

        yield TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client_with_auth(_patch_google):
    """App client with API_KEY enabled."""
    with patch("app.config.settings.api_key", "test-secret-key"):
        from fastapi.testclient import TestClient

        from app.main import app

        yield TestClient(app, raise_server_exceptions=False)


class TestAPIKeyAuth:
    """Verify API key middleware protects /api/* endpoints."""

    def test_health_accessible_without_key(self, client_with_auth):
        resp = client_with_auth.get("/health")
        assert resp.status_code == 200

    def test_metrics_accessible_without_key(self, client_with_auth):
        resp = client_with_auth.get("/metrics")
        assert resp.status_code == 200

    def test_api_endpoint_rejected_without_key(self, client_with_auth):
        resp = client_with_auth.get("/api/cost-summary")
        assert resp.status_code == 401
        assert "Invalid or missing API key" in resp.json()["detail"]

    def test_api_endpoint_rejected_with_wrong_key(self, client_with_auth):
        resp = client_with_auth.get(
            "/api/cost-summary",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 401

    def test_api_endpoint_allowed_with_correct_key(self, client_with_auth):
        resp = client_with_auth.get(
            "/api/cost-summary",
            headers={"Authorization": "Bearer test-secret-key"},
        )
        assert resp.status_code == 200

    def test_api_endpoints_open_when_key_not_set(self, client_no_auth):
        resp = client_no_auth.get("/api/cost-summary")
        assert resp.status_code == 200


class TestUploadValidation:
    """Verify file upload validation (size, content type, empty)."""

    def test_upload_empty_file_rejected(self, client_no_auth):
        resp = client_no_auth.post(
            "/api/upload-image",
            files={"file": ("test.jpg", b"", "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "Empty file" in resp.json()["detail"]

    def test_upload_wrong_content_type_rejected(self, client_no_auth):
        resp = client_no_auth.post(
            "/api/upload-image",
            files={"file": ("test.pdf", b"fake-pdf", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "JPG/PNG" in resp.json()["detail"]

    def test_upload_oversized_file_rejected(self, client_no_auth):
        with patch("app.config.settings.max_upload_size_mb", 1):
            # 1.5 MB file (over 1 MB limit)
            big_content = b"x" * (1024 * 1024 + 512 * 1024)
            resp = client_no_auth.post(
                "/api/upload-image",
                files={"file": ("big.jpg", big_content, "image/jpeg")},
            )
            assert resp.status_code == 413
            assert "too large" in resp.json()["detail"]


class TestSSRFValidation:
    """Verify the shared SSRF validator guards both single and CSV batch paths."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254/latest/meta-data/",
            "http://127.0.0.1:8500/secrets",
            "http://10.0.0.5/internal",
            "http://localhost/admin",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://svc.cluster.local/api",
            "file:///etc/passwd",
            "gopher://example.com/x",
        ],
    )
    def test_generate_request_blocks_internal_urls(self, url):
        from app.models.schemas import GenerateRequest

        with pytest.raises(ValueError):
            GenerateRequest(brief="test", product_image_url=url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254/latest/meta-data/",
            "http://localhost/admin",
            "file:///etc/passwd",
        ],
    )
    def test_product_create_blocks_internal_urls(self, url):
        """CSV batch path (ProductCreate.image_url) enforces the same SSRF policy."""
        from app.models.campaign_schemas import ProductCreate

        with pytest.raises(ValueError):
            ProductCreate(sku_id="S1", product_name="p", description="d", image_url=url)

    def test_public_urls_accepted_on_both_paths(self):
        from app.models.campaign_schemas import ProductCreate
        from app.models.schemas import GenerateRequest

        url = "https://cdn.example.com/product.jpg"
        assert GenerateRequest(brief="test", product_image_url=url).product_image_url == url
        product = ProductCreate(sku_id="S1", product_name="p", description="d", image_url=url)
        assert product.image_url == url

    def test_none_image_url_accepted(self):
        from app.models.campaign_schemas import ProductCreate

        product = ProductCreate(sku_id="S1", product_name="p", description="d", image_url=None)
        assert product.image_url is None


class TestTaskIdValidation:
    """Verify the task-id pattern accepts vendor formats but rejects injection shapes."""

    @pytest.mark.parametrize(
        "task_id",
        [
            "cgt-20260610-abc123",
            "dry-run-deadbeef",
            "task_with_underscores",
            "v1.2.3-task.id",
            "a" * 128,
        ],
    )
    def test_valid_task_ids_accepted(self, task_id):
        from app.main import _TASK_ID_RE

        assert _TASK_ID_RE.match(task_id)

    @pytest.mark.parametrize(
        "task_id",
        ["", "../etc/passwd", "id/with/slash", "id with space", "-leading-dash", "a" * 129],
    )
    def test_invalid_task_ids_rejected(self, task_id):
        from app.main import _TASK_ID_RE

        assert not _TASK_ID_RE.match(task_id)


class TestDashboardAuthSession:
    """Verify the dashboard session attaches the API key when configured."""

    def _load_dash_config(self, monkeypatch, api_key):
        import importlib
        from pathlib import Path

        if api_key is None:
            monkeypatch.delenv("API_KEY", raising=False)
        else:
            monkeypatch.setenv("API_KEY", api_key)
        dash_dir = str(Path(__file__).resolve().parents[2] / "dashboard")
        monkeypatch.syspath_prepend(dash_dir)
        import config as dash_config

        return importlib.reload(dash_config)

    def test_session_sends_bearer_header_when_key_set(self, monkeypatch):
        cfg = self._load_dash_config(monkeypatch, "dash-secret")
        assert cfg.api.headers["Authorization"] == "Bearer dash-secret"

    def test_session_has_no_auth_header_without_key(self, monkeypatch):
        cfg = self._load_dash_config(monkeypatch, None)
        assert "Authorization" not in cfg.api.headers
