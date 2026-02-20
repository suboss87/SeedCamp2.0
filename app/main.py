"""
D2C Video Ad Pipeline — FastAPI Application
AI-Powered Product Video Generation at Scale with ModelArk.
Matches the 5-step architecture from the Solution Brief.
"""
import asyncio
import json
import logging
import time

from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.schemas import (
    CostSummary,
    GenerateRequest,
    GenerateResponse,
    SKUTier,
    VideoTaskStatus,
)
from app.services import cost_tracker, video_gen
from app.services import firestore_client
from app.services.pipeline import run_pipeline
from app import monitoring
from app.routes.campaigns import router as campaigns_router
from app.utils.retry import validate_api_key, InvalidAPIKeyError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AdCamp: AI Content Generation Pipeline",
    description="""
    Reference architecture for cost-optimized AI content generation at scale,
    powered by BytePlus ModelArk.

    ## Architecture Patterns
    - **Tiered Model Routing**: Route workloads to premium or cost-optimized models based on business value
    - **Async Task Pipeline**: Submit → poll → result for long-running AI generation
    - **Token-Aware Cost Tracking**: Real-time cost attribution per request
    - **Batch Orchestration**: Semaphore-controlled concurrent generation
    - **Resilient API Integration**: Retry with backoff, rate-limit honoring, error classification

    ## Implementation: Video Generation
    - **Seed 1.8**: Script/copy generation (OpenAI-compatible)
    - **Seedance 1.5 Pro**: Premium-tier video ($1.20/M tokens)
    - **Seedance 1.0 Pro Fast**: Standard-tier video ($0.70/M tokens)
    - **Multi-format output**: TikTok (9:16), Instagram (1:1), YouTube (16:9)

    ## Adapt for Your Use Case
    Replace the video generation step with any AI model — image generation,
    audio synthesis, document creation — the pipeline patterns remain the same.
    """,
    version="1.0.0",
    contact={
        "name": "AdCamp Support",
        "url": "https://github.com/suboss87/adcamp",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS: wide-open for demo/reference use. Restrict allow_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")

# Register campaign routes
app.include_router(campaigns_router)

# Lazy import for GCS (used by /api/upload-image)
from google.cloud import storage


# ─── Shared Pipeline Helpers ─────────────────────────────────────────────────────

async def _run_pipeline(req: GenerateRequest) -> dict:
    """Thin wrapper: unpack GenerateRequest and call the extracted pipeline."""
    return await run_pipeline(
        brief=req.brief,
        sku_tier=req.sku_tier,
        sku_id=req.sku_id,
        product_image_url=req.product_image_url,
        platforms=[p.value for p in req.platforms] if req.platforms else ["tiktok"],
        duration=req.duration,
        resolution=req.resolution,
    )


def _track_success_metrics(cost_usd: float, sku_tier: SKUTier):
    """Track generation success metrics.
    Cost and per-tier counts are tracked automatically by cost_tracker.
    """
    monitoring.increment_counter("videos_generated_total")


# ─── Startup Events ───────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Validate configuration and initialize services on startup."""
    logger.info("Starting AdCamp D2C Video Ad Pipeline...")

    # Initialize Firestore
    try:
        firestore_client.init()
        logger.info("Firestore initialized")
    except Exception as e:
        logger.warning("Firestore init failed (continuing without persistence): %s", e)
    
    # Validate API key
    if not settings.ark_api_key:
        logger.error("ARK_API_KEY environment variable is not set!")
        raise InvalidAPIKeyError("ARK_API_KEY is required but not configured")
    
    logger.info("Validating ModelArk API key...")
    try:
        await validate_api_key(settings.ark_api_key, settings.ark_base_url)
        logger.info("✅ ModelArk API key validated successfully")
    except InvalidAPIKeyError as e:
        logger.error(f"❌ Invalid ModelArk API key: {e}")
        logger.error("Please check your ARK_API_KEY environment variable")
        raise
    except Exception as e:
        logger.warning(f"⚠️  Could not validate API key (continuing anyway): {e}")
    
    logger.debug("Configured models:")
    logger.debug(f"  Script: {settings.script_model}")
    logger.debug(f"  Video Pro: {settings.video_model_pro} ($1.20/M)")
    logger.debug(f"  Video Fast: {settings.video_model_fast} ($0.70/M)")
    logger.info("Pipeline ready 🚀")


# ─── Health ───────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "pipeline": "D2C Video Ad Pipeline",
        "models": {
            "script": settings.script_model,
            "video_pro": settings.video_model_pro,
            "video_fast": settings.video_model_fast,
        },
        "metrics": monitoring.get_metrics(),
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    monitoring.increment_counter("api_requests_total")
    return Response(content=monitoring.prometheus_format(), media_type="text/plain")


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health status with metrics and dependencies."""
    return monitoring.get_health_status()


# ─── Image Upload Endpoint ───────────────────────────────────────────────────────

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image to GCS and return a public URL.
    Expects content-type image/jpeg or image/png.
    """
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
            raise HTTPException(status_code=400, detail="Only JPG/PNG supported")

        # Upload to GCS
        client = storage.Client()
        bucket = client.bucket(settings.gcs_bucket)
        # Create a unique object name
        ts = int(time.time())
        blob_name = f"uploads/{ts}-{file.filename.replace(' ', '_')}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=file.content_type)
        # Make public
        blob.make_public()
        return {"url": blob.public_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image upload failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Full Pipeline (Steps 1-4) ──────────────────────────────────────────────────

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_ad(req: GenerateRequest):
    """
    D2C Video Ad Pipeline:
    1. INPUT:        Campaign brief + product image + SKU tier
    2. SEED 1.8:     Script generation (ad copy + Seedance prompt)
    3. MODEL ROUTER: Hero → Seedance Pro | Catalog → Pro Fast
    4. SEEDANCE:     Video generation (async)
    """
    monitoring.increment_counter("api_requests_total")

    try:
        result = await _run_pipeline(req)
        _track_success_metrics(result["cost"].total_cost_usd, req.sku_tier)

        return GenerateResponse(
            task_id=result["task_id"],
            sku_id=req.sku_id,
            sku_tier=req.sku_tier,
            status="Processing",
            script=result["script"],
            video=VideoTaskStatus(
                task_id=result["task_id"],
                status="Processing",
                model_used=result["model_id"],
            ),
            cost=result["cost"],
        )

    except Exception as e:
        monitoring.increment_counter("videos_failed_total")
        logger.exception("Pipeline failed for SKU %s", req.sku_id)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Video Status ─────────────────────────────────────────────────────────────────

@app.get("/api/status/{task_id}", response_model=VideoTaskStatus)
async def check_status(task_id: str):
    """Poll video generation status."""
    try:
        return await video_gen.get_video_status(task_id)
    except Exception as e:
        logger.exception("Status check failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wait/{task_id}", response_model=VideoTaskStatus)
async def wait_for_result(task_id: str):
    """Block until video is ready (for demo/testing)."""
    try:
        return await video_gen.wait_for_video(task_id)
    except Exception as e:
        logger.exception("Wait failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Cost Summary ─────────────────────────────────────────────────────────────────

@app.get("/api/cost-summary", response_model=CostSummary)
async def get_cost_summary():
    """Aggregate cost tracking — proves the $0.27/video target."""
    return cost_tracker.get_summary()


# ─── Streaming Generation (SSE for live progress) ────────────────────────────────

@app.post("/api/generate-stream")
async def generate_ad_stream(req: GenerateRequest):
    """
    D2C Video Ad Pipeline with Server-Sent Events (SSE) for live progress.
    Streams progress updates to the frontend in real-time.
    """
    async def event_generator():
        try:
            # Steps 1-4: Run pipeline
            yield f"data: {json.dumps({'step': 1, 'status': 'started', 'message': '🚀 Starting pipeline...', 'progress': 5})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'step': 2, 'status': 'running', 'message': '📝 Generating ad script with Seed 1.8...', 'progress': 15})}\n\n"
            result = await _run_pipeline(req)
            script = result["script"]
            task_id = result["task_id"]
            model_id = result["model_id"]

            model_name = "Seedance 1.5 Pro" if "1-5" in model_id else "Seedance 1.0 Pro Fast"
            yield f"data: {json.dumps({'step': 2, 'status': 'complete', 'message': f'✅ Script generated', 'progress': 35, 'data': {'script': script.dict(), 'tokens': {'input': result['in_tokens'], 'output': result['out_tokens']}}})}\n\n"
            yield f"data: {json.dumps({'step': 3, 'status': 'complete', 'message': f'✅ Routed to {model_name}', 'progress': 45, 'data': {'model': model_id, 'cost_per_m': result['cost_per_m']}})}\n\n"
            yield f"data: {json.dumps({'step': 4, 'status': 'complete', 'message': '✅ Video task created', 'progress': 55, 'data': {'task_id': task_id}})}\n\n"

            # Step 5: Poll for video completion
            yield f"data: {json.dumps({'step': 5, 'status': 'running', 'message': '⏳ Generating video (this may take 30-60s)...', 'progress': 60})}\n\n"

            max_wait = settings.poll_timeout
            poll_interval = settings.poll_interval
            elapsed = 0

            while elapsed < max_wait:
                status = await video_gen.get_video_status(task_id)

                if status.status == "Succeeded":
                    _track_success_metrics(result["cost"].total_cost_usd, req.sku_tier)
                    data_final = {
                        'step': 5, 'status': 'complete',
                        'message': '✅ Video generated successfully!',
                        'progress': 100,
                        'data': {'video_url': status.video_url, 'cost': result["cost"].dict(), 'script': script.dict()}
                    }
                    yield f"data: {json.dumps(data_final)}\n\n"
                    break

                elif status.status == "Failed":
                    monitoring.increment_counter("videos_failed_total")
                    yield f"data: {json.dumps({'step': 5, 'status': 'failed', 'message': f'❌ Generation failed: {status.error}', 'progress': 0})}\n\n"
                    break

                elapsed += poll_interval
                progress_pct = min(60 + (elapsed / max_wait) * 35, 95)
                yield f"data: {json.dumps({'step': 5, 'status': 'running', 'message': f'⏳ Generating... {elapsed}s elapsed', 'progress': int(progress_pct)})}\n\n"
                await asyncio.sleep(poll_interval)
            else:
                yield f"data: {json.dumps({'step': 5, 'status': 'timeout', 'message': f'⚠️ Timeout after {max_wait}s. Task ID: {task_id}', 'progress': 0, 'data': {'task_id': task_id}})}\n\n"

        except Exception as e:
            monitoring.increment_counter("videos_failed_total")
            logger.exception("Streaming pipeline failed")
            yield f"data: {json.dumps({'status': 'error', 'message': f'❌ Error: {str(e)}', 'progress': 0})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
