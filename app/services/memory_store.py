"""
In-Memory Persistence Backend
Drop-in replacement for firestore_client — stores campaigns, products, and
video results in memory. Used by default so the project runs without GCP.

Data is lost on restart. For production persistence, set PERSISTENCE_BACKEND=firestore.
"""

import logging
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from app.models.campaign_schemas import (
    Campaign,
    CampaignCreate,
    CampaignStatus,
    Product,
    ProductCreate,
    ProductStatus,
    VideoResult,
)

logger = logging.getLogger(__name__)

# In-memory collections
_campaigns: dict[str, dict] = {}
_products: dict[str, dict] = {}
_video_results: dict[str, dict] = {}


def init():
    """No-op for in-memory backend."""
    logger.info("Using in-memory persistence (data will not survive restarts)")


# ─── Campaigns ───────────────────────────────────────────────────────────────────


async def create_campaign(data: CampaignCreate) -> Campaign:
    now = datetime.now(timezone.utc)
    campaign = Campaign(
        id=uuid.uuid4().hex[:20],
        name=data.name,
        theme=data.theme,
        platforms=data.platforms,
        duration=data.duration,
        resolution=data.resolution,
        created_at=now,
        updated_at=now,
    )
    _campaigns[campaign.id] = campaign.model_dump()
    logger.info("Created campaign %s: %s", campaign.id, campaign.name)
    return campaign


async def get_campaign(campaign_id: str) -> Optional[Campaign]:
    data = _campaigns.get(campaign_id)
    if not data:
        return None
    return Campaign(**data)


async def list_campaigns(limit: int = 20, offset: int = 0) -> list[Campaign]:
    sorted_campaigns = sorted(
        _campaigns.values(), key=lambda c: c["created_at"], reverse=True
    )
    return [Campaign(**c) for c in sorted_campaigns[offset : offset + limit]]


async def update_campaign_status(campaign_id: str, status: CampaignStatus):
    if campaign_id in _campaigns:
        _campaigns[campaign_id]["status"] = status.value
        _campaigns[campaign_id]["updated_at"] = datetime.now(timezone.utc)


async def delete_campaign(campaign_id: str):
    _campaigns.pop(campaign_id, None)
    # Delete associated products and results
    product_ids = [
        pid for pid, p in _products.items() if p["campaign_id"] == campaign_id
    ]
    for pid in product_ids:
        _products.pop(pid, None)
    result_ids = [
        rid for rid, r in _video_results.items() if r["campaign_id"] == campaign_id
    ]
    for rid in result_ids:
        _video_results.pop(rid, None)
    logger.info("Deleted campaign %s and all associated data", campaign_id)


# ─── Products ────────────────────────────────────────────────────────────────────


async def create_product(campaign_id: str, data: ProductCreate) -> Product:
    product = Product(
        id=uuid.uuid4().hex[:20],
        campaign_id=campaign_id,
        sku_id=data.sku_id,
        product_name=data.product_name,
        description=data.description,
        image_url=data.image_url,
        sku_tier=data.sku_tier,
        category=data.category,
        created_at=datetime.now(timezone.utc),
    )
    _products[product.id] = product.model_dump()
    return product


async def create_products_batch(
    campaign_id: str, products: list[ProductCreate]
) -> list[Product]:
    created = []
    for data in products:
        product = await create_product(campaign_id, data)
        created.append(product)
    # Update campaign product count
    if campaign_id in _campaigns:
        _campaigns[campaign_id]["total_products"] = _campaigns[campaign_id].get(
            "total_products", 0
        ) + len(products)
        _campaigns[campaign_id]["updated_at"] = datetime.now(timezone.utc)
    logger.info("Created %d products for campaign %s", len(created), campaign_id)
    return created


async def list_products(campaign_id: str) -> list[Product]:
    return [
        Product(**p) for p in _products.values() if p["campaign_id"] == campaign_id
    ]


async def update_product_status(
    product_id: str, status: ProductStatus, brief: str = None
):
    if product_id in _products:
        _products[product_id]["status"] = status.value
        if brief is not None:
            _products[product_id]["generated_brief"] = brief


# ─── Video Results ────────────────────────────────────────────────────────────────


async def save_video_result(result: VideoResult):
    _video_results[result.id] = result.model_dump()


async def update_video_result(result_id: str, updates: dict):
    if result_id in _video_results:
        _video_results[result_id].update(updates)


async def list_video_results(campaign_id: str) -> list[VideoResult]:
    return [
        VideoResult(**r)
        for r in _video_results.values()
        if r["campaign_id"] == campaign_id
    ]


# ─── Campaign Counter Updates (atomic in-memory) ─────────────────────────────────


async def increment_campaign_completed(campaign_id: str, cost_usd: float):
    if campaign_id in _campaigns:
        _campaigns[campaign_id]["completed_videos"] = (
            _campaigns[campaign_id].get("completed_videos", 0) + 1
        )
        _campaigns[campaign_id]["total_cost_usd"] = (
            _campaigns[campaign_id].get("total_cost_usd", 0.0) + cost_usd
        )
        _campaigns[campaign_id]["updated_at"] = datetime.now(timezone.utc)


async def increment_campaign_failed(campaign_id: str):
    if campaign_id in _campaigns:
        _campaigns[campaign_id]["failed_videos"] = (
            _campaigns[campaign_id].get("failed_videos", 0) + 1
        )
        _campaigns[campaign_id]["updated_at"] = datetime.now(timezone.utc)
