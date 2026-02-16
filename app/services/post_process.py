"""
Post-Processing — FFmpeg
Step 5 of the D2C Pipeline: converts generated video to
platform-specific formats and aspect ratios.

TikTok:    9:16, 1080x1920 (or 720x1280)
Instagram: 1:1,  1080x1080 (or 720x720)
YouTube:   16:9, 1920x1080 (or 1280x720)
"""
import asyncio
import logging
import shutil
from pathlib import Path

from app.config import settings
from app.models.schemas import Platform, PlatformVariant

logger = logging.getLogger(__name__)

# Platform → (aspect_ratio, width, height)
PLATFORM_SPECS = {
    Platform.tiktok: ("9:16", 720, 1280),
    Platform.instagram: ("1:1", 720, 720),
    Platform.youtube: ("16:9", 1280, 720),
}


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


async def process_for_platforms(
    source_video: Path,
    platforms: list[Platform],
    sku_id: str,
) -> list[PlatformVariant]:
    """
    Convert a source video to platform-specific variants via FFmpeg.
    Falls back to copying the original if FFmpeg is not installed.
    """
    variants = []

    for platform in platforms:
        aspect, width, height = PLATFORM_SPECS[platform]
        output_name = f"{sku_id}_{platform.value}_{width}x{height}.mp4"
        output_path = settings.output_dir / output_name

        if _ffmpeg_available():
            # Scale + crop to exact dimensions, center crop
            cmd = [
                "ffmpeg", "-y", "-i", str(source_video),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                str(output_path),
            ]
            logger.info("FFmpeg: %s → %s (%s)", source_video.name, output_name, aspect)
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("FFmpeg failed for %s: %s", platform.value, stderr.decode()[-500:])
                # Fallback: copy original
                shutil.copy2(source_video, output_path)
        else:
            logger.warning("FFmpeg not installed — copying original for %s", platform.value)
            shutil.copy2(source_video, output_path)

        variants.append(PlatformVariant(
            platform=platform,
            file_path=str(output_path),
            aspect_ratio=aspect,
            resolution=f"{width}x{height}",
        ))

    return variants
