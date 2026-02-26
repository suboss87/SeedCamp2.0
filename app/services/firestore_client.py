"""
Firestore Client — Persistence Layer
CRUD operations for campaigns, products, and video results.
Uses AsyncClient for consistency with the async codebase.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

try:
    from google.cloud.firestore import AsyncClient
    from google.cloud import firestore
except ImportError:
    raise ImportError(
        "Firestore backend requires google-cloud-firestore. "
        "Install with: pip install -r requirements-gcp.txt"
    )

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

# Lazily initialized — call init() during app startup
_db: Optional[AsyncClient] = None


def init():
    """Initialize async Firestore client. Call once during app startup."""
    global _db
    _db = AsyncClient()
    logger.info("Firestore AsyncClient initialized")


def _get_db() -> AsyncClient:
    if _db is None:
        raise RuntimeError(
            "Firestore not initialized — call firestore_client.init() on startup"
        )
    return _db


# ─── Campaigns ───────────────────────────────────────────────────────────────────


async def create_campaign(data: CampaignCreate) -> Campaign:
    db = _get_db()
    doc_ref = db.collection("campaigns").document()
    now = datetime.now(timezone.utc)
    campaign = Campaign(
        id=doc_ref.id,
        name=data.name,
        theme=data.theme,
        platforms=data.platforms,
        duration=data.duration,
        resolution=data.resolution,
        created_at=now,
        updated_at=now,
    )
    await doc_ref.set(campaign.model_dump())
    logger.info("Created campaign %s: %s", campaign.id, campaign.name)
    return campaign


async def get_campaign(campaign_id: str) -> Optional[Campaign]:
    db = _get_db()
    doc = await db.collection("campaigns").document(campaign_id).get()
    if not doc.exists:
        return None
    return Campaign(**doc.to_dict())


async def list_campaigns(limit: int = 20, offset: int = 0) -> list[Campaign]:
    db = _get_db()
    query = (
        db.collection("campaigns")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .offset(offset)
    )
    docs = [doc async for doc in query.stream()]
    return [Campaign(**doc.to_dict()) for doc in docs]


async def update_campaign_status(campaign_id: str, status: CampaignStatus):
    db = _get_db()
    await db.collection("campaigns").document(campaign_id).update(
        {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc),
        }
    )


async def delete_campaign(campaign_id: str):
    """Delete campaign and all associated products and video results."""
    db = _get_db()
    # Delete products
    products_query = db.collection("products").where("campaign_id", "==", campaign_id)
    async for doc in products_query.stream():
        await doc.reference.delete()
    # Delete video results
    results_query = db.collection("video_results").where(
        "campaign_id", "==", campaign_id
    )
    async for doc in results_query.stream():
        await doc.reference.delete()
    # Delete campaign
    await db.collection("campaigns").document(campaign_id).delete()
    logger.info("Deleted campaign %s and all associated data", campaign_id)


# ─── Products ────────────────────────────────────────────────────────────────────


async def create_product(campaign_id: str, data: ProductCreate) -> Product:
    db = _get_db()
    doc_ref = db.collection("products").document()
    product = Product(
        id=doc_ref.id,
        campaign_id=campaign_id,
        sku_id=data.sku_id,
        product_name=data.product_name,
        description=data.description,
        image_url=data.image_url,
        sku_tier=data.sku_tier,
        category=data.category,
        created_at=datetime.now(timezone.utc),
    )
    await doc_ref.set(product.model_dump())
    return product


async def create_products_batch(
    campaign_id: str, products: list[ProductCreate]
) -> list[Product]:
    """Create multiple products and update campaign product count."""
    db = _get_db()
    created = []
    batch = db.batch()

    for data in products:
        doc_ref = db.collection("products").document()
        product = Product(
            id=doc_ref.id,
            campaign_id=campaign_id,
            sku_id=data.sku_id,
            product_name=data.product_name,
            description=data.description,
            image_url=data.image_url,
            sku_tier=data.sku_tier,
            category=data.category,
            created_at=datetime.now(timezone.utc),
        )
        batch.set(doc_ref, product.model_dump())
        created.append(product)

    # Update campaign product count
    campaign_ref = db.collection("campaigns").document(campaign_id)
    batch.update(
        campaign_ref,
        {
            "total_products": firestore.Increment(len(products)),
            "updated_at": datetime.now(timezone.utc),
        },
    )

    await batch.commit()
    logger.info("Created %d products for campaign %s", len(created), campaign_id)
    return created


async def list_products(campaign_id: str) -> list[Product]:
    db = _get_db()
    query = db.collection("products").where("campaign_id", "==", campaign_id)
    docs = [doc async for doc in query.stream()]
    return [Product(**doc.to_dict()) for doc in docs]


async def update_product_status(
    product_id: str, status: ProductStatus, brief: str = None
):
    db = _get_db()
    updates: dict = {"status": status.value}
    if brief is not None:
        updates["generated_brief"] = brief
    await db.collection("products").document(product_id).update(updates)


# ─── Video Results ────────────────────────────────────────────────────────────────


async def save_video_result(result: VideoResult):
    db = _get_db()
    doc_ref = db.collection("video_results").document(result.id)
    await doc_ref.set(result.model_dump())


async def update_video_result(result_id: str, updates: dict):
    db = _get_db()
    await db.collection("video_results").document(result_id).update(updates)


async def list_video_results(campaign_id: str) -> list[VideoResult]:
    db = _get_db()
    query = db.collection("video_results").where("campaign_id", "==", campaign_id)
    docs = [doc async for doc in query.stream()]
    return [VideoResult(**doc.to_dict()) for doc in docs]


# ─── Campaign Counter Updates (atomic) ───────────────────────────────────────────


async def increment_campaign_completed(campaign_id: str, cost_usd: float):
    """Atomically increment completed video count and total cost."""
    db = _get_db()
    await db.collection("campaigns").document(campaign_id).update(
        {
            "completed_videos": firestore.Increment(1),
            "total_cost_usd": firestore.Increment(cost_usd),
            "updated_at": datetime.now(timezone.utc),
        }
    )


async def increment_campaign_failed(campaign_id: str):
    """Atomically increment failed video count."""
    db = _get_db()
    await db.collection("campaigns").document(campaign_id).update(
        {
            "failed_videos": firestore.Increment(1),
            "updated_at": datetime.now(timezone.utc),
        }
    )
