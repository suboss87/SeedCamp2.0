"""Quality evaluation schemas for the video quality assessment layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QualityDimension(BaseModel):
    """Individual quality dimension assessment."""

    name: str = Field(..., description="Quality dimension name")
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Quality score (0.0 = poor, 1.0 = excellent)"
    )
    explanation: str = Field(..., description="Brief explanation of the assessment")


class QualityEvalResult(BaseModel):
    """Result of quality evaluation on a generated ad script and prompt."""

    overall_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate quality score")
    grade: Literal["excellent", "good", "fair", "poor"] = Field(
        ..., description="Quality grade based on overall_score"
    )
    dimensions: list[QualityDimension] = Field(
        default_factory=list, description="Per-dimension quality scores"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Actionable improvement suggestions"
    )
    eval_tokens_in: int = Field(0, description="Input tokens used for quality eval")
    eval_tokens_out: int = Field(0, description="Output tokens used for quality eval")
    eval_cost_usd: float = Field(0.0, description="Cost of quality evaluation in USD")
