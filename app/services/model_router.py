"""
Smart Model Router — Step 3 of the D2C Pipeline
Routes each SKU to the optimal Seedance model tier based on business value.

Hero SKUs (Top 20%)  → Seedance 1.5 Pro     ($1.20/M tokens, cinematic)
Catalog SKUs (80%)   → Seedance 1.0 Pro Fast ($0.70/M tokens, 3x faster)
"""
import logging

from app.config import settings
from app.models.schemas import SKUTier

logger = logging.getLogger(__name__)


def route(sku_tier: SKUTier) -> tuple[str, float]:
    """
    Select the video generation model based on SKU tier.
    Returns (model_id, cost_per_million_tokens).
    """
    if sku_tier == SKUTier.hero:
        model_id = settings.video_model_pro
        cost_per_m = settings.cost_per_m_seedance_pro
        logger.info("Routing HERO SKU → %s ($%.2f/M tokens)", model_id, cost_per_m)
    else:
        model_id = settings.video_model_fast
        cost_per_m = settings.cost_per_m_seedance_fast
        logger.info("Routing CATALOG SKU → %s ($%.2f/M tokens)", model_id, cost_per_m)

    return model_id, cost_per_m
