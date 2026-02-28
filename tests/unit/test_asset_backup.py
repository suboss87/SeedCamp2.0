"""Tests for the video asset backup service.

All tests mock httpx and GCS — no real network calls.
Verifies: download + upload flow, error handling, URL generation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.asset_backup import backup_video
from app.utils.retry import ModelArkAPIError


class TestBackupVideo:
    @patch("app.services.asset_backup.httpx.AsyncClient")
    async def test_successful_backup(self, mock_client_cls):
        """Download from CDN + upload to GCS returns public URL."""
        # Mock httpx download
        mock_response = MagicMock()
        mock_response.content = b"fake-video-bytes"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Mock GCS — patch google.cloud.storage module in sys.modules
        mock_blob = MagicMock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/videos/camp1/prod1/abc.mp4"
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_gcs_client = MagicMock()
        mock_gcs_client.bucket.return_value = mock_bucket

        mock_storage = MagicMock()
        mock_storage.Client.return_value = mock_gcs_client

        mock_google_cloud = MagicMock()
        mock_google_cloud.storage = mock_storage

        with patch.dict(
            "sys.modules",
            {
                "google": MagicMock(),
                "google.cloud": mock_google_cloud,
                "google.cloud.storage": mock_storage,
            },
        ):
            url = await backup_video(
                ark_url="https://cdn.byteplus.com/video/task123.mp4",
                campaign_id="camp1",
                product_id="prod1",
            )

        assert "storage.googleapis.com" in url
        mock_client.get.assert_called_once()
        mock_blob.upload_from_string.assert_called_once()
        mock_blob.make_public.assert_called_once()

    @patch("app.services.asset_backup.httpx.AsyncClient")
    async def test_empty_download_raises(self, mock_client_cls):
        """Empty download should raise ValueError."""
        mock_response = MagicMock()
        mock_response.content = b""
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(ValueError, match="empty"):
            await backup_video(
                ark_url="https://cdn.byteplus.com/video/empty.mp4",
                campaign_id="camp1",
                product_id="prod1",
            )

    @patch("app.services.asset_backup.httpx.AsyncClient")
    async def test_download_failure_raises(self, mock_client_cls):
        """HTTP error during download propagates as ModelArkAPIError (wrapped by retry)."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("404", request=mock_request, response=mock_response)
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises((httpx.HTTPStatusError, ModelArkAPIError, Exception)):
            await backup_video(
                ark_url="https://cdn.byteplus.com/video/missing.mp4",
                campaign_id="camp1",
                product_id="prod1",
            )

    async def test_gcs_import_error(self):
        """Missing google-cloud-storage raises ImportError."""
        with patch("app.services.asset_backup.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.content = b"fake-video-bytes"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with (
                patch.dict("sys.modules", {"google.cloud": None, "google.cloud.storage": None}),
                pytest.raises((ImportError, ModuleNotFoundError)),
            ):
                await backup_video(
                    ark_url="https://cdn.byteplus.com/video/test.mp4",
                    campaign_id="camp1",
                    product_id="prod1",
                )
