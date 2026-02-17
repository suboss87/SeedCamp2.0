"""
Video Generation — Seedance 1.5 Pro / 1.0 Pro Fast
Step 4 of the D2C Pipeline: asynchronous video generation with polling.
Model is selected by the Smart Router (step 3).
"""
import asyncio
import logging
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import VideoTaskStatus
from app.utils.retry import retry_with_backoff, parse_modelark_error

logger = logging.getLogger(__name__)

_BASE = settings.ark_base_url.rstrip("/")
_HEADERS = {
    "Authorization": f"Bearer {settings.ark_api_key}",
    "Content-Type": "application/json",
}


# Aspect-ratio map for platforms
_RATIO_MAP = {
    "tiktok": "9:16",
    "instagram": "1:1",
    "youtube": "16:9",
}


@retry_with_backoff(max_retries=3, initial_delay=2.0)
async def create_video_task(
    prompt: str,
    model_id: str,
    image_url: Optional[str] = None,
    duration: int = 5,
    resolution: str = "720p",
    ratio: str = "16:9",
) -> str:
    """
    Create an async video generation task via
    POST /api/v3/contents/generations/tasks
    model_id comes from the Smart Router.
    Returns the task_id for polling.
    
    Automatically retries on transient failures (network, 5xx, rate limits).
    """
    content = []
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    content.append({"type": "text", "text": prompt})

    payload = {
        "model": model_id,
        "content": content,
        "resolution": resolution,
        "ratio": ratio,
        "duration": duration,
        "watermark": False,
    }

    try:
        async with httpx.AsyncClient(timeout=90) as client:  # Increased timeout for large videos
            resp = await client.post(
                f"{_BASE}/contents/generations/tasks",
                headers=_HEADERS,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        # Parse ModelArk-specific error for better logging
        error = parse_modelark_error(e.response)
        logger.error(f"Failed to create video task: {error}")
        raise

    task_id = data.get("id", "")
    if not task_id:
        raise ValueError(f"No task ID returned from ModelArk API: {data}")
    
    logger.info("Created video task %s with model %s", task_id, model_id)
    return task_id


@retry_with_backoff(max_retries=2, initial_delay=1.0)
async def get_video_status(task_id: str, model_used: str = "") -> VideoTaskStatus:
    """Query the status of a video generation task via
    GET /api/v3/contents/generations/tasks/{task_id}
    
    Automatically retries on transient failures.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{_BASE}/contents/generations/tasks/{task_id}",
                headers=_HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        error = parse_modelark_error(e.response)
        logger.error(f"Failed to get video status for {task_id}: {error}")
        raise

    _STATUS_MAP = {
        "succeeded": "Succeeded",
        "failed": "Failed",
        "processing": "Running",
        "queued": "Running",
        "running": "Running",
    }

    raw_status = data.get("status", "Unknown")
    status = _STATUS_MAP.get(raw_status, raw_status)
    video_url = None
    error = None

    if status == "Succeeded":
        content = data.get("content", {})
        if isinstance(content, dict):
            video_url = content.get("video_url")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "video_url" in item:
                    video_url = item["video_url"]
                    break
    elif status == "Failed":
        error = data.get("error", {}).get("message", "Unknown error")

    return VideoTaskStatus(
        task_id=task_id,
        status=status,
        model_used=model_used,
        video_url=video_url,
        error=error,
    )


async def wait_for_video(task_id: str, model_used: str = "") -> VideoTaskStatus:
    """Poll until video is ready or timeout."""
    elapsed = 0
    while elapsed < settings.poll_timeout:
        result = await get_video_status(task_id, model_used)
        if result.status in ("Succeeded", "Failed"):
            return result
        logger.info("Task %s status: %s (waited %ds)", task_id, result.status, elapsed)
        await asyncio.sleep(settings.poll_interval)
        elapsed += settings.poll_interval

    return VideoTaskStatus(
        task_id=task_id,
        status="Timeout",
        model_used=model_used,
        error=f"Video generation timed out after {settings.poll_timeout}s",
    )
