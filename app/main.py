"""
D2C Video Ad Pipeline — FastAPI Application
AI-Powered Product Video Generation at Scale with ModelArk.
Matches the 6-step architecture from the Solution Brief.
"""
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.schemas import (
    CostSummary,
    GenerateRequest,
    GenerateResponse,
    VideoTaskStatus,
)
from app.services import cost_tracker, model_router, script_writer, video_gen

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="D2C Video Ad Pipeline",
    description="AI-powered product video generation at scale — BytePlus ModelArk POC",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")


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
    }


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
    try:
        # Step 2: Script generation via Seed 1.8
        logger.info("Step 2: Seed 1.8 — Generating ad script for SKU %s...", req.sku_id)
        script, in_tokens, out_tokens = await script_writer.generate_script(req.brief)

        # Step 3: Smart Model Router
        logger.info("Step 3: Routing SKU %s (tier=%s)...", req.sku_id, req.sku_tier.value)
        model_id, cost_per_m = model_router.route(req.sku_tier)

        # Step 4: Video generation via Seedance
        logger.info("Step 4: Seedance — Creating video task with %s...", model_id)
        task_id = await video_gen.create_video_task(
            prompt=script.video_prompt,
            model_id=model_id,
            image_url=req.product_image_url,
            duration=req.duration,
            resolution=req.resolution,
        )

        # Calculate cost (video tokens estimated from duration + resolution)
        # Actual tokens come from the API response when video completes
        est_video_tokens = _estimate_video_tokens(req.duration, req.resolution)
        cost = cost_tracker.calculate_cost(
            script_input_tokens=in_tokens,
            script_output_tokens=out_tokens,
            video_tokens=est_video_tokens,
            model_used=model_id,
            cost_per_m=cost_per_m,
            sku_tier=req.sku_tier,
        )

        return GenerateResponse(
            task_id=task_id,
            sku_id=req.sku_id,
            sku_tier=req.sku_tier,
            status="Processing",
            script=script,
            video=VideoTaskStatus(task_id=task_id, status="Processing", model_used=model_id),
            cost=cost,
        )

    except Exception as e:
        logger.exception("Pipeline failed for SKU %s", req.sku_id)
        raise HTTPException(status_code=500, detail=str(e))


def _estimate_video_tokens(duration: int, resolution: str) -> int:
    """Estimate video tokens: (W * H * FPS * Duration) / 1024."""
    res_map = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
    w, h = res_map.get(resolution, (1280, 720))
    fps = 24
    return int((w * h * fps * duration) / 1024)


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
