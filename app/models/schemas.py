from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SKUTier(str, Enum):
    hero = "hero"        # Top 20% — Seedance 1.5 Pro
    catalog = "catalog"  # 80% — Seedance 1.0 Pro Fast


class Platform(str, Enum):
    tiktok = "tiktok"        # 9:16
    instagram = "instagram"  # 1:1
    youtube = "youtube"      # 16:9


# ---- Requests ----

class GenerateRequest(BaseModel):
    """D2C Video Ad Pipeline input."""
    brief: str = Field(..., description="Campaign brief, e.g. 'Summer collection, beach vibes, energetic'")
    product_image_url: Optional[str] = Field(None, description="Public URL of the product image")
    sku_tier: SKUTier = SKUTier.catalog
    sku_id: str = Field("SKU-001", description="Product SKU identifier")
    platforms: list[Platform] = Field(
        default=[Platform.tiktok],
        description="Target platforms for post-processing",
    )
    duration: int = Field(8, ge=2, le=12)
    resolution: str = "720p"
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "brief": "Summer running campaign, energetic and dynamic vibes, urban streets at golden hour",
                    "sku_tier": "catalog",
                    "sku_id": "SHOE-001",
                    "platforms": ["tiktok", "instagram"],
                    "duration": 5,
                    "resolution": "720p"
                },
                {
                    "brief": "Luxury watch showcase, elegant and sophisticated, minimalist studio setting",
                    "product_image_url": "https://example.com/product.jpg",
                    "sku_tier": "hero",
                    "sku_id": "WATCH-PREMIUM-001",
                    "platforms": ["youtube"],
                    "duration": 10,
                    "resolution": "1080p"
                }
            ]
        }


# ---- Script Output (from Seed 1.8) ----

class AdScript(BaseModel):
    """Generated ad script and video prompt from Seed 1.8."""
    ad_copy: str = Field(..., description="Short ad copy / headline")
    scene_description: str = Field(..., description="Visual scene description")
    video_prompt: str = Field(..., description="Optimized Seedance video generation prompt")
    camera_direction: str = Field(..., description="Camera movement instruction")


# ---- Video Task ----

class VideoTaskStatus(BaseModel):
    task_id: str
    status: str  # Queued, Running, Succeeded, Failed, Timeout
    model_used: str = ""
    video_url: Optional[str] = None
    error: Optional[str] = None


# ---- Cost ----

class CostBreakdown(BaseModel):
    script_input_tokens: int = 0
    script_output_tokens: int = 0
    script_cost_usd: float = 0.0
    video_tokens: int = 0
    video_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    model_used: str = ""
    cost_per_m_tokens: float = 0.0


# ---- Full Response ----

class GenerateResponse(BaseModel):
    task_id: str
    sku_id: str
    sku_tier: SKUTier
    status: str
    script: AdScript
    video: VideoTaskStatus
    cost: CostBreakdown


# ---- Cost Summary ----

class CostSummary(BaseModel):
    total_videos: int = 0
    total_cost_usd: float = 0.0
    avg_cost_per_video: float = 0.0
    hero_videos: int = 0
    catalog_videos: int = 0
    hero_cost_usd: float = 0.0
    catalog_cost_usd: float = 0.0
