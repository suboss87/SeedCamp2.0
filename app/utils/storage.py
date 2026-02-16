import base64
import uuid
from pathlib import Path

import httpx

from app.config import settings


def save_base64_image(data: str, prefix: str = "thumb") -> Path:
    """Decode a base64 image and save to output dir. Returns the file path."""
    ext = "png"
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = settings.output_dir / filename
    filepath.write_bytes(base64.b64decode(data))
    return filepath


async def download_file(url: str, prefix: str = "video") -> Path:
    """Download a file from URL and save locally."""
    ext = url.rsplit(".", 1)[-1].split("?")[0] if "." in url else "mp4"
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = settings.output_dir / filename
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)
    return filepath
