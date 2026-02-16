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

logger = logging.getLogger(__name__)

_BASE = settings.ark_base_url.rstrip("/")
_HEADERS = {
    "Authorization": f"Bearer {settings.ark_api_key}",
    "Content-Type": "application/json",
}


async def create_video_task(
    prompt: str,
    model_id: str,
    image_url: Optional[str] = None,
    duration: int = 8,
    resolution: str = "720p",
) -> str:
    """
    Create an async video generation task.
    model_id comes from the Smart Router.
    Returns the task_id for polling.
    """
    content = []
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    prompt_with_params = f"{prompt} --dur {duration} --res {resolution}"
    content.append({"type": "text", "text": prompt_with_params})

    payload = {
        "model": model_id,
        "content": content,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{_BASE}/video/generations",
            headers=_HEADERS,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    task_id = data.get("id", "")
    logger.info("Created video task %s with model %s", task_id, model_id)
    return task_id


async def get_video_status(task_id: str, model_used: str = "") -> VideoTaskStatus:
    """Query the status of a video generation task."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{_BASE}/video/generations/{task_id}",
            headers=_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()

    status = data.get("status", "Unknown")
    video_url = None
    error = None

    if status == "Succeeded":
        content = data.get("content", [])
        for item in content:
            if item.get("type") == "video_url":
                video_url = item.get("video_url", {}).get("url")
                break
        if not video_url:
            video_url = data.get("video_url")
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
