from __future__ import annotations

import ipaddress
from enum import Enum
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_public_http_url(v: str | None, field_name: str) -> str | None:
    """Reject URLs that could be used for SSRF (internal hosts, private IPs, non-HTTP schemes).

    Shared by every schema field whose URL is fetched server-side.
    """
    if v is None:
        return v
    parsed = urlparse(v)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"{field_name} must use http or https")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError(f"{field_name} must have a valid hostname")
    # Block IP literals pointing to private/internal/loopback ranges
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise ValueError(f"{field_name} must not target private or internal addresses")
    except ValueError as exc:
        if "must not target" in str(exc):
            raise
        # Not a valid IP literal — it's a hostname; check well-known internal names
    blocked = {"localhost", "metadata.google.internal"}
    if host in blocked or host.endswith(".internal") or host.endswith(".local"):
        raise ValueError(f"{field_name} must not target internal hostnames")
    return v


class SKUTier(str, Enum):
    hero = "hero"  # Top 20% -- Seedance 2.0
    catalog = "catalog"  # 80% -- Seedance 2.0 Fast


class Platform(str, Enum):
    tiktok = "tiktok"  # 9:16
    instagram = "instagram"  # 1:1
    youtube = "youtube"  # 16:9


# ---- Requests ----


class GenerateRequest(BaseModel):
    """Video Generation Pipeline input."""

    brief: str = Field(
        ...,
        max_length=2000,
        description="Campaign brief, e.g. 'Summer collection, beach vibes, energetic'",
    )
    product_image_url: str | None = Field(None, description="Public URL of the product image")

    @field_validator("product_image_url")
    @classmethod
    def block_ssrf(cls, v: str | None) -> str | None:
        return validate_public_http_url(v, "product_image_url")

    sku_tier: SKUTier = SKUTier.catalog
    sku_id: str = Field("SKU-001", description="Product SKU identifier")
    platforms: list[Platform] = Field(
        default=[Platform.tiktok],
        description="Target platforms for post-processing",
    )
    duration: int = Field(8, ge=2, le=15)
    resolution: str = "720p"
    sound: bool = Field(default=True, description="Enable native audio in generated video")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "brief": "Summer running campaign, energetic and dynamic vibes, urban streets at golden hour",
                    "sku_tier": "catalog",
                    "sku_id": "SHOE-001",
                    "platforms": ["tiktok", "instagram"],
                    "duration": 5,
                    "resolution": "720p",
                },
                {
                    "brief": "Luxury watch showcase, elegant and sophisticated, minimalist studio setting",
                    "product_image_url": "https://example.com/product.jpg",
                    "sku_tier": "hero",
                    "sku_id": "WATCH-PREMIUM-001",
                    "platforms": ["youtube"],
                    "duration": 10,
                    "resolution": "1080p",
                },
            ],
        }
    )


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
    video_url: str | None = None
    error: str | None = None


# ---- Cost ----


class CostBreakdown(BaseModel):
    script_input_tokens: int = 0
    script_output_tokens: int = 0
    script_cost_usd: float = 0.0
    video_tokens: int = 0
    video_cost_usd: float = 0.0
    safety_eval_cost_usd: float = 0.0
    quality_eval_cost_usd: float = 0.0
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
    safety: dict | None = None
    quality: dict | None = None


# ---- Cost Summary ----


class CostSummary(BaseModel):
    total_videos: int = 0
    total_cost_usd: float = 0.0
    avg_cost_per_video: float = 0.0
    hero_videos: int = 0
    catalog_videos: int = 0
    hero_cost_usd: float = 0.0
    catalog_cost_usd: float = 0.0
