"""
AdCamp — FastAPI Application
AI-Powered Video Generation at Scale with BytePlus ModelArk.
Implements the 5-step pipeline: Input → Script Gen → Smart Router → Video Gen → Output.
"""

import asyncio
import json
import logging
import os
import uuid

from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

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
from app.services.pipeline import run_pipeline, ContentBlockedError
from app import monitoring
from app.routes.campaigns import router as campaigns_router
from app.utils.retry import validate_api_key, InvalidAPIKeyError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AdCamp: AI Content Generation Pipeline",
    description="""
    Reference architecture for cost-optimized AI video generation at scale,
    powered by BytePlus ModelArk.

    ## Architecture Patterns
    - **Tiered Model Routing**: Route workloads to premium or cost-optimized models based on business value
    - **Async Task Pipeline**: Submit → poll → result for long-running AI generation
    - **Token-Aware Cost Tracking**: Real-time cost attribution per request
    - **Batch Orchestration**: Semaphore-controlled concurrent generation
    - **Resilient API Integration**: Retry with backoff, rate-limit honoring, error classification

    ## Models
    - **Seed 1.8**: Script/copy generation (OpenAI-compatible)
    - **Seedance Pro**: Premium-tier video ($1.20/M tokens)
    - **Seedance Pro Fast**: Standard-tier video ($0.70/M tokens)

    ## Adapt for Your Use Case
    Replace tiers, model IDs, and the video generation step to match your
    industry and AI provider — the pipeline patterns remain the same.
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

# Rate limiting: configurable via RATE_LIMIT env var (slowapi format, e.g. "60/minute").
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: configurable via CORS_ORIGINS env var (comma-separated).
# Defaults to "*" for demo/reference use. Restrict in production.
_cors_origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key authentication middleware.
# When API_KEY is set in env, all /api/* requests require Authorization: Bearer <key>.
# Health, metrics, and docs endpoints remain open.
_PUBLIC_PATHS = {
    "/health",
    "/health/detailed",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
}


@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    if settings.api_key and request.url.path.startswith("/api"):
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {settings.api_key}":
            return JSONResponse(
                status_code=401, content={"detail": "Invalid or missing API key"}
            )
    return await call_next(request)


app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")

# Register campaign routes
app.include_router(campaigns_router)

# Lazy import for GCS (used by /api/upload-image)
from google.cloud import storage  # noqa: E402

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
    logger.info("Starting AdCamp Video Generation Pipeline...")

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
        logger.info("ModelArk API key validated successfully")
    except InvalidAPIKeyError as e:
        logger.error("Invalid ModelArk API key: %s", e)
        logger.error("Please check your ARK_API_KEY environment variable")
        raise
    except Exception as e:
        logger.warning(
            "Could not validate API key at startup (network issue or endpoint unreachable). "
            "The API key may still be valid — pipeline calls will fail if it is not. Error: %s",
            e,
        )

    logger.debug("Configured models:")
    logger.debug("  Script: %s", settings.script_model)
    logger.debug("  Video Pro: %s ($1.20/M)", settings.video_model_pro)
    logger.debug("  Video Fast: %s ($0.70/M)", settings.video_model_fast)
    logger.info("Pipeline ready")


# ─── Health ───────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "pipeline": "AdCamp Video Generation Pipeline",
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
@limiter.limit(settings.rate_limit)
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Upload an image to GCS and return a public URL.
    Expects content-type image/jpeg or image/png.
    """
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({len(content) / 1024 / 1024:.1f}MB). Max: {settings.max_upload_size_mb}MB",
            )
        if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
            raise HTTPException(status_code=400, detail="Only JPG/PNG supported")

        # Validate magic bytes match declared content type
        _MAGIC_JPEG = b"\xff\xd8\xff"
        _MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
        if content[:3] == _MAGIC_JPEG:
            detected = "image/jpeg"
        elif content[:8] == _MAGIC_PNG:
            detected = "image/png"
        else:
            raise HTTPException(
                status_code=400,
                detail="File content does not match a valid JPEG or PNG image",
            )
        if file.content_type == "image/jpg":
            declared = "image/jpeg"
        else:
            declared = file.content_type
        if detected != declared:
            raise HTTPException(
                status_code=400,
                detail="Content-Type header does not match actual file content",
            )

        # Upload to GCS — use UUID to prevent directory traversal
        client = storage.Client()
        bucket = client.bucket(settings.gcs_bucket)
        safe_name = (
            os.path.basename(file.filename or "image") if file.filename else "image"
        )
        ext = os.path.splitext(safe_name)[1] or (
            ".jpg" if detected == "image/jpeg" else ".png"
        )
        blob_name = f"uploads/{uuid.uuid4().hex}{ext}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=detected)
        # Make public
        blob.make_public()
        return {"url": blob.public_url}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Image upload failed")
        raise HTTPException(status_code=500, detail="Image upload failed")


# ─── Full Pipeline (Steps 1-4) ──────────────────────────────────────────────────


@app.post("/api/generate", response_model=GenerateResponse)
@limiter.limit(settings.rate_limit)
async def generate_ad(request: Request, req: GenerateRequest):
    """
    Video Generation Pipeline:
    1. INPUT:        Campaign brief + product image + SKU tier
    2. SCRIPT GEN:   Seed 1.8 generates copy + Seedance prompt
    3. SMART ROUTER: Hero → Seedance Pro | Catalog → Pro Fast
    4. VIDEO GEN:    Async video generation with polling
    """
    monitoring.increment_counter("api_requests_total")

    try:
        result = await _run_pipeline(req)
        _track_success_metrics(result["cost"].total_cost_usd, req.sku_tier)

        safety_data = None
        if result.get("safety"):
            safety_data = result["safety"].model_dump()

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
            safety=safety_data,
        )

    except ContentBlockedError as e:
        logger.warning("Content blocked for SKU %s: %s", req.sku_id, e)
        raise HTTPException(
            status_code=422,
            detail={
                "error": "content_blocked",
                "message": str(e),
                "safety": e.safety_result.model_dump(),
            },
        )

    except Exception:
        monitoring.increment_counter("videos_failed_total")
        logger.exception("Pipeline failed for SKU %s", req.sku_id)
        raise HTTPException(
            status_code=500,
            detail="Video generation pipeline failed. Check server logs for details.",
        )


# ─── Video Status ─────────────────────────────────────────────────────────────────


@app.get("/api/status/{task_id}", response_model=VideoTaskStatus)
async def check_status(task_id: str):
    """Poll video generation status."""
    try:
        return await video_gen.get_video_status(task_id)
    except Exception:
        logger.exception("Status check failed for task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to check video status")


@app.get("/api/wait/{task_id}", response_model=VideoTaskStatus)
async def wait_for_result(task_id: str):
    """Block until video is ready (for demo/testing)."""
    try:
        return await video_gen.wait_for_video(task_id)
    except Exception:
        logger.exception("Wait failed for task %s", task_id)
        raise HTTPException(
            status_code=500, detail="Failed while waiting for video result"
        )


# ─── Cost Summary ─────────────────────────────────────────────────────────────────


@app.get("/api/cost-summary", response_model=CostSummary)
async def get_cost_summary():
    """Aggregate cost tracking across all generated videos."""
    return cost_tracker.get_summary()


# ─── Safety Summary ──────────────────────────────────────────────────────────


@app.get("/api/safety-summary")
async def get_safety_summary():
    """Aggregate safety evaluation metrics."""
    metrics = monitoring.get_metrics()
    checks = metrics["safety_checks_total"]
    flagged = metrics["safety_flagged_total"]
    blocked = metrics["safety_blocked_total"]
    return {
        "safety_enabled": settings.safety_enabled,
        "total_checks": checks,
        "total_flagged": flagged,
        "total_blocked": blocked,
        "block_rate": round(blocked / checks, 4) if checks > 0 else 0.0,
        "flag_rate": round(flagged / checks, 4) if checks > 0 else 0.0,
        "avg_eval_seconds": metrics["safety_eval_avg_seconds"],
    }


# ─── Streaming Generation (SSE for live progress) ────────────────────────────────


@app.post("/api/generate-stream")
@limiter.limit(settings.rate_limit)
async def generate_ad_stream(request: Request, req: GenerateRequest):
    """
    Video Generation Pipeline with Server-Sent Events (SSE) for live progress.
    Streams progress updates to the frontend in real-time.
    """

    async def event_generator():
        try:
            # Steps 1-4: Run pipeline
            yield f"data: {json.dumps({'step': 1, 'status': 'started', 'message': 'Starting pipeline...', 'progress': 5})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'step': 2, 'status': 'running', 'message': 'Generating ad script with Seed 1.8...', 'progress': 15})}\n\n"
            try:
                result = await _run_pipeline(req)
            except ContentBlockedError as e:
                yield f"data: {json.dumps({'step': 2, 'status': 'complete', 'message': 'Script generated', 'progress': 30})}\n\n"
                yield f"data: {json.dumps({'step': 'safety', 'status': 'blocked', 'message': f'Content blocked by safety evaluation (score={e.safety_result.overall_score:.2f})', 'progress': 0, 'data': {'safety': e.safety_result.model_dump()}})}\n\n"
                return
            script = result["script"]
            task_id = result["task_id"]
            model_id = result["model_id"]

            safety_msg = ""
            if result.get("safety"):
                safety = result["safety"]
                safety_msg = f" (safety: {safety.risk_level})"
            model_name = (
                "Seedance 1.5 Pro" if "1-5" in model_id else "Seedance 1.0 Pro Fast"
            )
            yield f"data: {json.dumps({'step': 2, 'status': 'complete', 'message': f'Script generated{safety_msg}', 'progress': 35, 'data': {'script': script.model_dump(), 'tokens': {'input': result['in_tokens'], 'output': result['out_tokens']}}})}\n\n"
            yield f"data: {json.dumps({'step': 3, 'status': 'complete', 'message': f'Routed to {model_name}', 'progress': 45, 'data': {'model': model_id, 'cost_per_m': result['cost_per_m']}})}\n\n"
            yield f"data: {json.dumps({'step': 4, 'status': 'complete', 'message': 'Video task created', 'progress': 55, 'data': {'task_id': task_id}})}\n\n"

            # Step 5: Poll for video completion
            yield f"data: {json.dumps({'step': 5, 'status': 'running', 'message': 'Generating video (this may take 30-60s)...', 'progress': 60})}\n\n"

            max_wait = settings.poll_timeout
            poll_interval = settings.poll_interval
            elapsed = 0

            while elapsed < max_wait:
                status = await video_gen.get_video_status(task_id)

                if status.status == "Succeeded":
                    _track_success_metrics(result["cost"].total_cost_usd, req.sku_tier)
                    data_final = {
                        "step": 5,
                        "status": "complete",
                        "message": "Video generated successfully",
                        "progress": 100,
                        "data": {
                            "video_url": status.video_url,
                            "cost": result["cost"].model_dump(),
                            "script": script.model_dump(),
                        },
                    }
                    yield f"data: {json.dumps(data_final)}\n\n"
                    break

                elif status.status == "Failed":
                    monitoring.increment_counter("videos_failed_total")
                    yield f"data: {json.dumps({'step': 5, 'status': 'failed', 'message': f'Generation failed: {status.error}', 'progress': 0})}\n\n"
                    break

                elapsed += poll_interval
                progress_pct = min(60 + (elapsed / max_wait) * 35, 95)
                yield f"data: {json.dumps({'step': 5, 'status': 'running', 'message': f'Generating... {elapsed}s elapsed', 'progress': int(progress_pct)})}\n\n"
                await asyncio.sleep(poll_interval)
            else:
                yield f"data: {json.dumps({'step': 5, 'status': 'timeout', 'message': f'Timeout after {max_wait}s. Task ID: {task_id}', 'progress': 0, 'data': {'task_id': task_id}})}\n\n"

        except Exception:
            monitoring.increment_counter("videos_failed_total")
            logger.exception("Streaming pipeline failed")
            yield f"data: {json.dumps({'status': 'error', 'message': 'Pipeline error. Check server logs for details.', 'progress': 0})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
