"""
Batch Generator — Campaign-scale video generation
Orchestrates brief generation + pipeline execution for multiple products
with semaphore-based concurrency and per-product error handling.
"""
import asyncio
import logging
from datetime import datetime

from app.models.campaign_schemas import (
    Campaign,
    CampaignStatus,
    Product,
    ProductStatus,
    VideoResult,
)
from app.models.schemas import SKUTier
from app.services import brief_generator, firestore_client as db, video_gen
from app.services.pipeline import run_pipeline

logger = logging.getLogger(__name__)


async def run_batch(campaign: Campaign, products: list[Product], concurrency: int = 3):
    """Run batch video generation for a campaign.

    Runs as a background task (fire-and-forget from the endpoint).
    Each product goes through: brief → pipeline → wait → save result.
    """
    semaphore = asyncio.Semaphore(concurrency)
    logger.info(
        "Starting batch for campaign %s: %d products, concurrency=%d",
        campaign.id, len(products), concurrency,
    )

    async def process_one(product: Product):
        async with semaphore:
            await _process_product(campaign, product)

    # Run all products concurrently (bounded by semaphore)
    await asyncio.gather(*[process_one(p) for p in products], return_exceptions=True)

    # Determine final campaign status
    updated = await db.get_campaign(campaign.id)
    if updated.completed_videos == updated.total_products:
        final_status = CampaignStatus.completed
    elif updated.completed_videos > 0:
        final_status = CampaignStatus.partial
    else:
        final_status = CampaignStatus.failed

    await db.update_campaign_status(campaign.id, final_status)
    logger.info(
        "Batch complete for campaign %s: %d completed, %d failed → %s",
        campaign.id, updated.completed_videos, updated.failed_videos, final_status.value,
    )


async def _process_product(campaign: Campaign, product: Product):
    """Process a single product: brief → pipeline → wait → save."""
    result_id = f"{campaign.id}_{product.id}"

    # Create initial video result record
    video_result = VideoResult(
        id=result_id,
        campaign_id=campaign.id,
        product_id=product.id,
        task_id="",
        status="generating",
        created_at=datetime.utcnow(),
    )
    await db.save_video_result(video_result)
    await db.update_product_status(product.id, ProductStatus.generating)

    try:
        # Stage A: Generate brief
        brief, _, _ = await brief_generator.generate_brief(
            campaign_theme=campaign.theme,
            product_name=product.product_name,
            description=product.description,
            sku_tier=product.sku_tier,
            category=product.category,
        )
        await db.update_product_status(product.id, ProductStatus.generating, brief=brief)

        # Stage B + C + D: Run pipeline (script → route → video)
        sku_tier = SKUTier.hero if product.sku_tier == "hero" else SKUTier.catalog
        pipeline_result = await run_pipeline(
            brief=brief,
            sku_tier=sku_tier,
            sku_id=product.sku_id,
            product_image_url=product.image_url,
            platforms=campaign.platforms,
            duration=campaign.duration,
            resolution=campaign.resolution,
        )

        task_id = pipeline_result["task_id"]
        await db.update_video_result(result_id, {"task_id": task_id})

        # Wait for video completion
        video_status = await video_gen.wait_for_video(task_id, pipeline_result["model_id"])

        if video_status.status == "Succeeded":
            await db.update_video_result(result_id, {
                "status": "completed",
                "video_url": video_status.video_url,
                "model_used": pipeline_result["model_id"],
                "script": pipeline_result["script"].model_dump(),
                "cost": pipeline_result["cost"].model_dump(),
                "completed_at": datetime.utcnow(),
            })
            await db.update_product_status(product.id, ProductStatus.completed)
            await db.increment_campaign_completed(campaign.id, pipeline_result["cost"].total_cost_usd)
            logger.info("Product %s completed: %s", product.sku_id, video_status.video_url)
        else:
            error_msg = video_status.error or f"Video generation {video_status.status}"
            await _mark_failed(result_id, product.id, campaign.id, error_msg)

    except Exception as e:
        logger.exception("Failed to process product %s", product.sku_id)
        await _mark_failed(result_id, product.id, campaign.id, str(e))


async def _mark_failed(result_id: str, product_id: str, campaign_id: str, error: str):
    """Mark a product and its video result as failed, increment campaign counter."""
    await db.update_video_result(result_id, {
        "status": "failed",
        "error": error,
        "completed_at": datetime.utcnow(),
    })
    await db.update_product_status(product_id, ProductStatus.failed)
    await db.increment_campaign_failed(campaign_id)
