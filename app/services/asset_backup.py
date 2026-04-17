"""
Asset Backup -- Video URL Permanence
Downloads generated videos from BytePlus CDN and uploads to GCS
for permanent storage. Non-blocking: backup failure doesn't affect delivery.
"""

import logging
import uuid

import httpx

from app.config import settings
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


@retry_with_backoff(max_retries=2, initial_delay=2.0)
async def backup_video(
    ark_url: str,
    campaign_id: str,
    product_id: str,
) -> str:
    """Download video from BytePlus CDN and upload to GCS.

    Returns the public GCS URL for the backed-up video.
    """
    # Download video from CDN
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.get(ark_url)
        response.raise_for_status()
        video_bytes = response.content

    if not video_bytes:
        raise ValueError("Downloaded video is empty")

    # Upload to GCS
    try:
        from google.cloud import storage
    except ImportError:
        raise ImportError(
            "Video backup requires google-cloud-storage. "
            "Install with: pip install google-cloud-storage"
        ) from None

    gcs_client = storage.Client()
    bucket = gcs_client.bucket(settings.gcs_bucket)
    blob_name = f"videos/{campaign_id}/{product_id}/{uuid.uuid4().hex}.mp4"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(video_bytes, content_type="video/mp4")
    blob.make_public()

    logger.info("Backed up video to GCS: %s", blob.public_url)
    return blob.public_url
