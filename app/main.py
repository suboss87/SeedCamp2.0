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
from app.services import cost_tracker, model_router, script_writer, video_gen
from app import monitoring
from app.utils.retry import validate_api_key, InvalidAPIKeyError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AdCamp: D2C Video Ad Pipeline",
    description="""
    Enterprise-ready AI video generation pipeline for e-commerce at scale.
    
    ## Features
    - **Smart Model Routing**: Hero SKUs → Seedance Pro | Catalog → Pro Fast
    - **Multi-Platform**: TikTok (9:16), Instagram (1:1), YouTube (16:9)
    - **Cost-Optimized**: $0.08/video average (50% under target)
    - **Observable**: Prometheus metrics, health checks, cost tracking
    
    ## Models Used
    - **Seed 1.8**: Script generation ($0.25/$2.00 per M tokens)
    - **Seedance 1.5 Pro**: Hero videos ($1.20/M tokens)
    - **Seedance 1.0 Pro Fast**: Catalog videos ($0.70/M tokens)
    
    ## Rate Limits
    - API calls: Limited by BytePlus ModelArk API quotas
    - Video generation: 2-10 concurrent tasks (recommended)
    
    ## Cost Implications
    - Script generation: ~$0.002/video
    - Video generation: $0.076-0.132/video (depends on SKU tier)
    - Total: $0.078-0.134/video
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")

# Lazy import for GCS (used by /api/upload-image)
from google.cloud import storage


# ─── Shared Pipeline Helpers ─────────────────────────────────────────────────────

def _estimate_video_tokens(duration: int, resolution: str) -> int:
    """Estimate video tokens: (W * H * FPS * Duration) / 1024."""
    res_map = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
    w, h = res_map.get(resolution, (1280, 720))
    fps = 24
    return int((w * h * fps * duration) / 1024)


async def _run_pipeline(req: GenerateRequest) -> dict:
    """Execute the 4-step pipeline (script → route → video → cost).
    Returns dict with script, model_id, cost_per_m, task_id, cost, in_tokens, out_tokens.
    """
    # Step 2: Script generation via Seed 1.8
    logger.info("Step 2: Seed 1.8 — Generating ad script for SKU %s...", req.sku_id)
    script_start = time.time()
    script, in_tokens, out_tokens = await script_writer.generate_script(req.brief)
    monitoring.record_duration("script_generation_duration_seconds", time.time() - script_start)

    # Step 3: Smart Model Router
    logger.info("Step 3: Routing SKU %s (tier=%s)...", req.sku_id, req.sku_tier.value)
    model_id, cost_per_m = model_router.route(req.sku_tier)

    # Step 4: Video generation via Seedance
    primary_platform = req.platforms[0].value if req.platforms else "tiktok"
    ratio = video_gen._RATIO_MAP.get(primary_platform, "16:9")
    logger.info("Step 4: Seedance — Creating video task with %s (ratio=%s)...", model_id, ratio)
    video_start = time.time()
    task_id = await video_gen.create_video_task(
        prompt=script.video_prompt,
        model_id=model_id,
        image_url=req.product_image_url,
        duration=req.duration,
        resolution=req.resolution,
        ratio=ratio,
    )
    monitoring.record_duration("video_generation_duration_seconds", time.time() - video_start)

    # Calculate cost
    est_video_tokens = _estimate_video_tokens(req.duration, req.resolution)
    cost = cost_tracker.calculate_cost(
        script_input_tokens=in_tokens,
        script_output_tokens=out_tokens,
        video_tokens=est_video_tokens,
        model_used=model_id,
        cost_per_m=cost_per_m,
        sku_tier=req.sku_tier,
    )

    return {
        "script": script,
        "model_id": model_id,
        "cost_per_m": cost_per_m,
        "task_id": task_id,
        "cost": cost,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
    }


def _track_success_metrics(cost_usd: float, sku_tier: SKUTier):
    """Track generation success metrics.
    Cost and per-tier counts are tracked automatically by cost_tracker.
    """
    monitoring.increment_counter("videos_generated_total")


# ─── Startup Events ───────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    logger.info("Starting AdCamp D2C Video Ad Pipeline...")
    
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
    
    logger.info("Configured models:")
    logger.info(f"  Script: {settings.script_model}")
    logger.info(f"  Video Pro: {settings.video_model_pro} ($1.20/M)")
    logger.info(f"  Video Fast: {settings.video_model_fast} ($0.70/M)")
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
