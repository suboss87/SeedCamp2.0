"""
Batch Generator -- Campaign-scale video generation
Orchestrates brief generation + pipeline execution for multiple products
with semaphore-based concurrency and per-product error handling.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.config import settings
from app.models.campaign_schemas import (
    Campaign,
    CampaignStatus,
    Product,
    ProductStatus,
    VideoResult,
)
from app.models.schemas import SKUTier
from app.services.notifications import NotificationEvent, notify
from app.services.persistence import db
from app.services.pipeline import run_pipeline

# In dry-run mode, use simulated stubs
if settings.dry_run:
    from app.services import dry_run as asset_backup
    from app.services import dry_run as brief_generator
    from app.services import dry_run as video_gen
else:
    from app.services import asset_backup, brief_generator, video_gen

logger = logging.getLogger(__name__)


async def run_batch(campaign: Campaign, products: list[Product], concurrency: int = 3):
    """Run batch video generation for a campaign.

    Runs as a background task (fire-and-forget from the endpoint).
    Each product goes through: brief → pipeline → wait → save result.
    """
    semaphore = asyncio.Semaphore(concurrency)
    logger.info(
        "Starting batch for campaign %s: %d products, concurrency=%d",
        campaign.id,
        len(products),
        concurrency,
    )

    async def process_one(product: Product):
        async with semaphore:
            await _process_product(campaign, product)

    # Run all products concurrently (bounded by semaphore)
    results = await asyncio.gather(*[process_one(p) for p in products], return_exceptions=True)
    for product, result in zip(products, results, strict=True):
        if isinstance(result, Exception):
            logger.error("Unhandled exception for product %s: %s", product.sku_id, result)

    # Determine final campaign status
    updated = await db.get_campaign(campaign.id)
    # Check for skipped products (budget enforcement)
    all_products = await db.list_products(campaign.id)
    skipped_count = sum(1 for p in all_products if p.status == ProductStatus.skipped)

    if updated.completed_videos == updated.total_products:
        final_status = CampaignStatus.completed
    elif updated.completed_videos > 0 or skipped_count > 0:
        final_status = CampaignStatus.partial
    else:
        final_status = CampaignStatus.failed

    await db.update_campaign_status(campaign.id, final_status)
    logger.info(
        "Batch complete for campaign %s: %d completed, %d failed → %s",
        campaign.id,
        updated.completed_videos,
        updated.failed_videos,
        final_status.value,
    )

    # Fire notification
    asyncio.create_task(
        notify(
            NotificationEvent.batch_complete,
            {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "completed": updated.completed_videos,
                "failed": updated.failed_videos,
                "skipped": skipped_count,
                "total_cost_usd": updated.total_cost_usd,
                "status": final_status.value,
                "message": f"{updated.completed_videos} completed, {updated.failed_videos} failed, {skipped_count} skipped",
            },
        )
    )


async def _check_budget(campaign: Campaign) -> bool:
    """Check if campaign budget is exceeded. Returns True if over budget."""
    if campaign.budget_limit_usd is None:
        return False
    updated = await db.get_campaign(campaign.id)
    return bool(updated and updated.total_cost_usd >= campaign.budget_limit_usd)


async def _process_product(campaign: Campaign, product: Product):
    """Process a single product: brief → pipeline → wait → save."""
    result_id = f"{campaign.id}_{product.id}"

    # Budget pre-check: skip product if budget exceeded
    if await _check_budget(campaign):
        logger.info(
            "Budget exceeded for campaign %s -- skipping product %s", campaign.id, product.sku_id
        )
        await db.update_product_status(product.id, ProductStatus.skipped)
        asyncio.create_task(
            notify(
                NotificationEvent.budget_exceeded,
                {
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "skipped_sku": product.sku_id,
                    "budget_limit_usd": campaign.budget_limit_usd,
                    "message": f"Budget limit ${campaign.budget_limit_usd:.2f} exceeded -- skipping {product.sku_id}",
                },
            )
        )
        return

    # Create initial video result record
    video_result = VideoResult(
        id=result_id,
        campaign_id=campaign.id,
        product_id=product.id,
        task_id="",
        status="generating",
        created_at=datetime.now(timezone.utc),
    )
    await db.save_video_result(video_result)
    await db.update_product_status(product.id, ProductStatus.generating)

    try:
        # Stage A: Generate brief
        brief, brief_in_tokens, brief_out_tokens = await brief_generator.generate_brief(
            campaign_theme=campaign.theme,
            product_name=product.product_name,
            description=product.description,
            sku_tier=product.sku_tier,
            category=product.category,
        )
        logger.info(
            "Brief generated for %s (%d in, %d out tokens)",
            product.sku_id,
            brief_in_tokens,
            brief_out_tokens,
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
            sound=settings.video_sound,
        )

        # Add brief generation cost to the pipeline cost breakdown
        brief_cost = (brief_in_tokens / 1_000_000) * settings.cost_per_m_seed18_input + (
            brief_out_tokens / 1_000_000
        ) * settings.cost_per_m_seed18_output
        pipeline_result["cost"].total_cost_usd = round(
            pipeline_result["cost"].total_cost_usd + brief_cost, 6
        )

        task_id = pipeline_result["task_id"]
        await db.update_video_result(result_id, {"task_id": task_id})

        # Wait for video completion
        video_status = await video_gen.wait_for_video(task_id, pipeline_result["model_id"])

        if video_status.status == "Succeeded":
            result_updates = {
                "status": "completed",
                "video_url": video_status.video_url,
                "ark_video_url": video_status.video_url,
                "model_used": pipeline_result["model_id"],
                "script": pipeline_result["script"].model_dump(),
                "cost": pipeline_result["cost"].model_dump(),
                "completed_at": datetime.now(timezone.utc),
            }

            # Non-blocking GCS backup
            try:
                gcs_url = await asset_backup.backup_video(
                    video_status.video_url, campaign.id, product.id
                )
                result_updates["gcs_video_url"] = gcs_url
                result_updates["gcs_backup_status"] = "completed"
                result_updates["video_url"] = gcs_url  # Prefer permanent URL
                logger.info("Video backed up for %s: %s", product.sku_id, gcs_url)
            except Exception:
                logger.warning("GCS backup failed for %s -- using CDN URL", product.sku_id)
                result_updates["gcs_backup_status"] = "failed"

            await db.update_video_result(result_id, result_updates)
            await db.update_product_status(product.id, ProductStatus.completed)
            await db.increment_campaign_completed(
                campaign.id, pipeline_result["cost"].total_cost_usd
            )
            logger.info("Product %s completed: %s", product.sku_id, video_status.video_url)
        else:
            error_msg = video_status.error or f"Video generation {video_status.status}"
            await _mark_failed(result_id, product.id, campaign.id, error_msg)

    except Exception as e:
        logger.exception("Failed to process product %s", product.sku_id)
        await _mark_failed(result_id, product.id, campaign.id, str(e))


async def regenerate_product(campaign: Campaign, product: Product, result_id: str):
    """Re-run pipeline for a single product (used by reject + regenerate flow).

    Resets the product status and creates a fresh pipeline run.
    """
    logger.info("Regenerating product %s (result %s)", product.sku_id, result_id)

    # Reset product status to pending, then process
    await db.update_product_status(product.id, ProductStatus.pending)

    # Delete old result, re-process will create a new one
    await db.update_video_result(result_id, {"status": "regenerating"})

    await _process_product(campaign, product)


async def _mark_failed(result_id: str, product_id: str, campaign_id: str, error: str):
    """Mark a product and its video result as failed, increment campaign counter."""
    await db.update_video_result(
        result_id,
        {
            "status": "failed",
            "error": error,
            "completed_at": datetime.now(timezone.utc),
        },
    )
    await db.update_product_status(product_id, ProductStatus.failed)
    await db.increment_campaign_failed(campaign_id)

    asyncio.create_task(
        notify(
            NotificationEvent.video_failed,
            {
                "campaign_id": campaign_id,
                "product_id": product_id,
                "error": error,
                "message": f"Video generation failed for {product_id}: {error}",
            },
        )
    )
