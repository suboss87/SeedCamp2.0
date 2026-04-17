"""
Dry-Run Stubs -- Simulate API Calls Without a ModelArk Key
When DRY_RUN=true, these functions replace the real script_writer,
video_gen, and safety_evaluator to let you explore the full pipeline
(routing, cost tracking, batching) with zero API cost and no credentials.

Usage:
    DRY_RUN=true make dev
"""

import asyncio
import logging
import uuid

from app.models.quality_schemas import QualityDimension, QualityEvalResult
from app.models.safety_schemas import SafetyCategory, SafetyEvalResult
from app.models.schemas import AdScript, VideoTaskStatus

logger = logging.getLogger(__name__)

# ─── Script Writer Stub ──────────────────────────────────────────────────────────


async def generate_script(brief: str) -> tuple[AdScript, int, int]:
    """Simulate Seed 1.8 script generation."""
    logger.info("[DRY-RUN] Generating simulated script for: %s", brief[:60])
    await asyncio.sleep(0.3)  # Simulate latency

    script = AdScript(
        ad_copy=f"[DRY-RUN] Captivating ad for: {brief[:40]}...",
        scene_description="Golden hour urban setting, dynamic camera work, product in motion",
        video_prompt=(
            "A cinematic product showcase: the item rotates slowly on a reflective surface, "
            "warm studio rim lighting with subtle lens flare, slow dolly-in revealing texture "
            "and detail, shallow depth of field, professional commercial quality."
        ),
        camera_direction="Slow dolly-in with slight orbit, rack focus on product details",
    )
    # Simulate realistic token counts
    input_tokens = 450
    output_tokens = 180
    return script, input_tokens, output_tokens


# ─── Video Generation Stub ───────────────────────────────────────────────────────

# Aspect-ratio map (mirrors real video_gen)
RATIO_MAP = {
    "tiktok": "9:16",
    "instagram": "1:1",
    "youtube": "16:9",
}

# Track simulated tasks
_simulated_tasks: dict[str, dict] = {}


async def create_video_task(
    prompt: str,
    model_id: str,
    image_url=None,
    duration: int = 5,
    resolution: str = "720p",
    ratio: str = "16:9",
    sound: bool = True,
) -> str:
    """Simulate creating a video generation task."""
    task_id = f"dry-run-{uuid.uuid4().hex[:12]}"
    _simulated_tasks[task_id] = {
        "model_id": model_id,
        "status": "Running",
        "created": True,
    }
    logger.info(
        "[DRY-RUN] Created simulated video task %s (model=%s, %ss, %s)",
        task_id,
        model_id,
        duration,
        resolution,
    )
    return task_id


async def get_video_status(task_id: str, model_used: str = "") -> VideoTaskStatus:
    """Simulate checking video status -- always returns Succeeded."""
    return VideoTaskStatus(
        task_id=task_id,
        status="Succeeded",
        model_used=model_used,
        video_url=f"https://example.com/dry-run/{task_id}.mp4",
    )


async def wait_for_video(task_id: str, model_used: str = "") -> VideoTaskStatus:
    """Simulate waiting for video -- returns after a short delay."""
    logger.info("[DRY-RUN] Simulating video generation wait for %s", task_id)
    await asyncio.sleep(1.0)  # Simulate some wait time
    return await get_video_status(task_id, model_used)


# ─── Safety Evaluator Stub ───────────────────────────────────────────────────────


async def evaluate_content_safety(
    script: AdScript,
) -> tuple[SafetyEvalResult, int, int]:
    """Simulate content safety evaluation -- always returns safe."""
    logger.info("[DRY-RUN] Simulating safety evaluation")
    await asyncio.sleep(0.1)

    categories = [
        SafetyCategory(name=cat, score=0.02, explanation="[DRY-RUN] No concerns")
        for cat in [
            "bias",
            "stereotypes",
            "violence",
            "sexual_content",
            "hate_speech",
            "cultural_insensitivity",
            "brand_safety",
        ]
    ]

    result = SafetyEvalResult(
        overall_score=0.02,
        risk_level="safe",
        categories=categories,
        flagged_issues=[],
        recommendation="proceed",
        eval_tokens_in=280,
        eval_tokens_out=120,
        eval_cost_usd=0.000310,
    )
    return result, 280, 120


# ─── Quality Evaluator Stub ─────────────────────────────────────────────────────


async def evaluate_video_quality(
    script: AdScript,
    brief: str = "",
    platforms: list[str] | None = None,
) -> tuple[QualityEvalResult, int, int]:
    """Simulate quality evaluation -- always returns good quality."""
    logger.info("[DRY-RUN] Simulating quality evaluation")
    await asyncio.sleep(0.1)

    dimensions = [
        QualityDimension(name=dim, score=0.78, explanation="[DRY-RUN] Good quality")
        for dim in [
            "prompt_clarity",
            "brand_alignment",
            "creative_quality",
            "technical_precision",
            "platform_fit",
        ]
    ]

    result = QualityEvalResult(
        overall_score=0.78,
        grade="good",
        dimensions=dimensions,
        suggestions=["[DRY-RUN] Consider adding more specific brand elements"],
        eval_tokens_in=320,
        eval_tokens_out=140,
        eval_cost_usd=0.000360,
    )
    return result, 320, 140


# ─── Asset Backup Stub ───────────────────────────────────────────────────────────


async def backup_video(
    ark_url: str,
    campaign_id: str,
    product_id: str,
) -> str:
    """Simulate video backup to GCS."""
    logger.info("[DRY-RUN] Simulating video backup for %s/%s", campaign_id, product_id)
    await asyncio.sleep(0.2)
    return f"https://storage.googleapis.com/dry-run-bucket/videos/{campaign_id}/{product_id}/backup.mp4"


# ─── Brief Generator Stub ────────────────────────────────────────────────────────


async def generate_brief(
    campaign_theme: str,
    product_name: str,
    description: str,
    sku_tier: str = "catalog",
    category: str = None,
) -> tuple[str, int, int]:
    """Simulate brief generation."""
    logger.info("[DRY-RUN] Generating simulated brief for: %s", product_name)
    await asyncio.sleep(0.2)

    tier_style = "premium cinematic" if sku_tier == "hero" else "punchy, fast-paced"
    brief = (
        f"[DRY-RUN] A {tier_style} video showcasing {product_name}. "
        f"{description[:80]}. {campaign_theme}. "
        f"Dynamic motion, studio lighting, professional finish."
    )
    return brief, 350, 100


# ─── Notification Stub ──────────────────────────────────────────────────────────


async def notify(event: str, payload: dict):
    """Simulate notification -- just logs."""
    logger.info("[DRY-RUN] Notification: %s -- %s", event, payload.get("message", ""))
