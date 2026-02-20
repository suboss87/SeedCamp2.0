"""
Cost Tracker
Tracks token usage and calculates cost per video generation.
"""
import logging
from typing import Optional

from app.config import settings
from app.models.schemas import CostBreakdown, CostSummary, SKUTier

logger = logging.getLogger(__name__)

# In-memory store (replace with DB in production)
_history: list[dict] = []


def calculate_cost(
    script_input_tokens: int,
    script_output_tokens: int,
    video_tokens: int,
    model_used: str,
    cost_per_m: float,
    sku_tier: SKUTier,
) -> CostBreakdown:
    """Calculate the cost breakdown for a single video generation."""
    script_cost = (
        (script_input_tokens / 1_000_000) * settings.cost_per_m_seed18_input
        + (script_output_tokens / 1_000_000) * settings.cost_per_m_seed18_output
    )
    video_cost = (video_tokens / 1_000_000) * cost_per_m
    total = round(script_cost + video_cost, 6)

    breakdown = CostBreakdown(
        script_input_tokens=script_input_tokens,
        script_output_tokens=script_output_tokens,
        script_cost_usd=round(script_cost, 6),
        video_tokens=video_tokens,
        video_cost_usd=round(video_cost, 6),
        total_cost_usd=total,
        model_used=model_used,
        cost_per_m_tokens=cost_per_m,
    )

    # Log to history
    _history.append({
        "sku_tier": sku_tier.value,
        "total_cost": total,
        "model": model_used,
    })

    logger.info(
        "Cost: script=$%.4f video=$%.4f total=$%.4f (model=%s)",
        script_cost, video_cost, total, model_used,
    )
    return breakdown


def get_summary() -> CostSummary:
    """Aggregate cost summary across all generated videos."""
    if not _history:
        return CostSummary()

    total = sum(h["total_cost"] for h in _history)
    hero = [h for h in _history if h["sku_tier"] == "hero"]
    catalog = [h for h in _history if h["sku_tier"] == "catalog"]

    return CostSummary(
        total_videos=len(_history),
        total_cost_usd=round(total, 4),
        avg_cost_per_video=round(total / len(_history), 4) if _history else 0,
        hero_videos=len(hero),
        catalog_videos=len(catalog),
        hero_cost_usd=round(sum(h["total_cost"] for h in hero), 4),
        catalog_cost_usd=round(sum(h["total_cost"] for h in catalog), 4),
    )
