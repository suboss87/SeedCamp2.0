"""
Smart Model Router — Step 3 of the Pipeline
Routes each SKU to the optimal Seedance model tier based on business value.

Hero SKUs (Top 20%)  → Seedance 1.5 Pro     ($1.20/M tokens, cinematic)
Catalog SKUs (80%)   → Seedance 1.0 Pro Fast ($0.70/M tokens, 3x faster)
"""
import logging

from app.config import settings
from app.models.schemas import SKUTier

logger = logging.getLogger(__name__)


_ROUTES = {
    SKUTier.hero: lambda: (settings.video_model_pro, settings.cost_per_m_seedance_pro),
    SKUTier.catalog: lambda: (settings.video_model_fast, settings.cost_per_m_seedance_fast),
}


def route(sku_tier: SKUTier) -> tuple[str, float]:
    """Select the video generation model based on SKU tier.
    Returns (model_id, cost_per_million_tokens).
    """
    model_id, cost_per_m = _ROUTES[sku_tier]()
    logger.info("Routing %s SKU → %s ($%.2f/M tokens)", sku_tier.value.upper(), model_id, cost_per_m)
    return model_id, cost_per_m
