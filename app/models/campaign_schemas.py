"""
Campaign Pydantic Models
Data models for campaigns, products, video results, and batch operations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# ─── Enums ───────────────────────────────────────────────────────────────────────


class CampaignStatus(str, Enum):
    draft = "draft"
    generating = "generating"
    completed = "completed"
    partial = "partial"  # some videos succeeded, some failed
    failed = "failed"


class ProductStatus(str, Enum):
    pending = "pending"
    generating = "generating"
    completed = "completed"
    failed = "failed"


# ─── Campaign ────────────────────────────────────────────────────────────────────


class CampaignCreate(BaseModel):
    """Input for creating a new campaign."""

    name: str = Field(..., min_length=1, max_length=200)
    theme: str = Field(
        ...,
        min_length=1,
        description="Campaign theme/brief used for auto-brief generation",
    )
    platforms: list[str] = Field(default=["tiktok"])
    duration: int = Field(default=8, ge=2, le=15)
    resolution: str = Field(default="720p")


class Campaign(BaseModel):
    """Full campaign document (mirrors Firestore)."""

    id: str
    name: str
    theme: str
    status: CampaignStatus = CampaignStatus.draft
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    total_products: int = 0
    completed_videos: int = 0
    failed_videos: int = 0
    total_cost_usd: float = 0.0
    platforms: list[str] = Field(default=["tiktok"])
    duration: int = 8
    resolution: str = "720p"


# ─── Product ─────────────────────────────────────────────────────────────────────


class ProductCreate(BaseModel):
    """Single product from CSV row."""

    sku_id: str
    product_name: str
    description: str
    image_url: Optional[str] = None
    sku_tier: str = "catalog"  # "hero" or "catalog"
    category: Optional[str] = None


class Product(BaseModel):
    """Full product document (mirrors Firestore)."""

    id: str
    campaign_id: str
    sku_id: str
    product_name: str
    description: str
    image_url: Optional[str] = None
    sku_tier: str = "catalog"
    category: Optional[str] = None
    generated_brief: Optional[str] = None
    status: ProductStatus = ProductStatus.pending
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Video Result ────────────────────────────────────────────────────────────────


class VideoResult(BaseModel):
    """Video generation result document (mirrors Firestore)."""

    id: str
    campaign_id: str
    product_id: str
    task_id: str
    status: str = "pending"
    video_url: Optional[str] = None
    error: Optional[str] = None
    model_used: str = ""
    script: Optional[dict] = None  # AdScript as dict
    cost: Optional[dict] = None  # CostBreakdown as dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# ─── Batch / Progress ────────────────────────────────────────────────────────────


class BatchProgress(BaseModel):
    """Polling response for batch generation progress."""

    campaign_id: str
    status: CampaignStatus
    total_products: int
    completed_videos: int
    failed_videos: int
    total_cost_usd: float
    progress_pct: float = 0.0


class BatchGenerateRequest(BaseModel):
    """Request to start batch generation for a campaign."""

    concurrency: int = Field(default=3, ge=1, le=10)


# ─── CSV Upload ──────────────────────────────────────────────────────────────────


class CSVUploadResult(BaseModel):
    """Result of CSV file parsing and product creation."""

    products_created: int
    products_skipped: int
    errors: list[str] = []
