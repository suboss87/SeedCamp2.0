"""
Pipeline — Core video generation logic
Extracted from main.py so it can be called by both single-video
endpoints and the batch generator.
"""

import logging
import time
from typing import Optional

from app.models.schemas import SKUTier
from app.services import cost_tracker, model_router, script_writer, video_gen
from app import monitoring

logger = logging.getLogger(__name__)


def _estimate_video_tokens(duration: int, resolution: str) -> int:
    """Estimate video tokens: (W * H * FPS * Duration) / 1024."""
    res_map = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
    w, h = res_map.get(resolution, (1280, 720))
    fps = 24
    return int((w * h * fps * duration) / 1024)


async def run_pipeline(
    brief: str,
    sku_tier: SKUTier,
    sku_id: str = "SKU-001",
    product_image_url: Optional[str] = None,
    platforms: Optional[list[str]] = None,
    duration: int = 8,
    resolution: str = "720p",
) -> dict:
    """Execute the 4-step pipeline (script -> route -> video -> cost).

    Returns dict with: script, model_id, cost_per_m, task_id, cost, in_tokens, out_tokens.
    """
    if platforms is None:
        platforms = ["tiktok"]

    # Step 2: Script generation via Seed 1.8
    logger.info("Step 2: Seed 1.8 — Generating ad script for SKU %s...", sku_id)
    script_start = time.time()
    script, in_tokens, out_tokens = await script_writer.generate_script(brief)
    monitoring.record_duration(
        "script_generation_duration_seconds", time.time() - script_start
    )

    # Step 3: Smart Model Router
    logger.info("Step 3: Routing SKU %s (tier=%s)...", sku_id, sku_tier.value)
    model_id, cost_per_m = model_router.route(sku_tier)

    # Step 4: Video generation via Seedance
    primary_platform = platforms[0] if platforms else "tiktok"
    ratio = video_gen._RATIO_MAP.get(primary_platform, "16:9")
    logger.info(
        "Step 4: Seedance — Creating video task with %s (ratio=%s)...", model_id, ratio
    )
    video_start = time.time()
    task_id = await video_gen.create_video_task(
        prompt=script.video_prompt,
        model_id=model_id,
        image_url=product_image_url,
        duration=duration,
        resolution=resolution,
        ratio=ratio,
    )
    monitoring.record_duration(
        "video_generation_duration_seconds", time.time() - video_start
    )

    # Calculate cost
    est_video_tokens = _estimate_video_tokens(duration, resolution)
    cost = cost_tracker.calculate_cost(
        script_input_tokens=in_tokens,
        script_output_tokens=out_tokens,
        video_tokens=est_video_tokens,
        model_used=model_id,
        cost_per_m=cost_per_m,
        sku_tier=sku_tier,
    )

    return {
        "script": script,
        "model_id": model_id,
        "cost_per_m": cost_per_m,
        "task_id": task_id,
        "cost": cost,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
    }
