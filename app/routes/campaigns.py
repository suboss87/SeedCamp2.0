"""
Campaign API Routes
CRUD operations, CSV upload, batch generation, progress polling, results.
"""

import logging

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.campaign_schemas import (
    BatchGenerateRequest,
    BatchProgress,
    Campaign,
    CampaignCreate,
    CampaignStatus,
    CSVUploadResult,
    Product,
    VideoResult,
)
from app.services import firestore_client as db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


# ─── Campaign CRUD ───────────────────────────────────────────────────────────────


@router.post("", response_model=Campaign)
async def create_campaign(data: CampaignCreate):
    """Create a new campaign."""
    campaign = await db.create_campaign(data)
    return campaign


@router.get("", response_model=list[Campaign])
async def list_campaigns(limit: int = 20, offset: int = 0):
    """List campaigns ordered by creation date (newest first)."""
    return await db.list_campaigns(limit=limit, offset=offset)


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: str):
    """Get a single campaign by ID."""
    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign and all associated products and results."""
    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await db.delete_campaign(campaign_id)
    return {"status": "deleted", "campaign_id": campaign_id}


# ─── Products (CSV Upload + List) ────────────────────────────────────────────────


@router.post("/{campaign_id}/products", response_model=CSVUploadResult)
async def upload_products_csv(campaign_id: str, file: UploadFile = File(...)):
    """Upload a CSV of products for a campaign.
    Required columns: sku_id, product_name, description.
    Optional columns: image_url, sku_tier, category.
    """
    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    from app.services.csv_parser import parse_csv

    products, errors = parse_csv(text)

    if not products and errors:
        raise HTTPException(
            status_code=400, detail=f"CSV parsing failed: {'; '.join(errors)}"
        )

    created = await db.create_products_batch(campaign_id, products)

    return CSVUploadResult(
        products_created=len(created),
        products_skipped=len(errors),
        errors=errors[:10],  # Cap error list
    )


@router.get("/{campaign_id}/products", response_model=list[Product])
async def list_products(campaign_id: str):
    """List all products in a campaign."""
    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await db.list_products(campaign_id)


# ─── Batch Generation ────────────────────────────────────────────────────────────


@router.post("/{campaign_id}/generate")
async def start_batch_generation(
    campaign_id: str, req: BatchGenerateRequest = BatchGenerateRequest()
):
    """Start batch video generation for all pending products in a campaign.
    Returns immediately — poll /progress for status.
    """
    import asyncio
    from app.services import batch_generator

    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status == CampaignStatus.generating:
        raise HTTPException(
            status_code=409, detail="Batch generation already in progress"
        )

    products = await db.list_products(campaign_id)
    pending = [p for p in products if p.status == "pending"]
    if not pending:
        raise HTTPException(status_code=400, detail="No pending products to generate")

    # Update campaign status
    await db.update_campaign_status(campaign_id, CampaignStatus.generating)

    # Fire-and-forget: run batch in background
    asyncio.create_task(
        batch_generator.run_batch(campaign, pending, concurrency=req.concurrency)
    )

    return {
        "status": "started",
        "campaign_id": campaign_id,
        "total_products": len(pending),
        "concurrency": req.concurrency,
    }


@router.get("/{campaign_id}/progress", response_model=BatchProgress)
async def get_batch_progress(campaign_id: str):
    """Poll batch generation progress (lightweight — reads one campaign doc)."""
    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    total = campaign.total_products
    done = campaign.completed_videos + campaign.failed_videos
    pct = (done / total * 100) if total > 0 else 0.0

    return BatchProgress(
        campaign_id=campaign_id,
        status=campaign.status,
        total_products=total,
        completed_videos=campaign.completed_videos,
        failed_videos=campaign.failed_videos,
        total_cost_usd=campaign.total_cost_usd,
        progress_pct=round(pct, 1),
    )


@router.get("/{campaign_id}/results", response_model=list[VideoResult])
async def list_video_results(campaign_id: str):
    """Get all video results for a campaign."""
    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await db.list_video_results(campaign_id)
