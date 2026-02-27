"""Safety evaluation schemas for the Responsible AI content safety layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SafetyCategory(BaseModel):
    """Individual safety category assessment."""

    name: str = Field(..., description="Safety category name")
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Risk score (0.0 = safe, 1.0 = high risk)"
    )
    explanation: str = Field(..., description="Brief explanation of the assessment")


class SafetyEvalResult(BaseModel):
    """Result of content safety evaluation on a generated ad script."""

    overall_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate risk score")
    risk_level: Literal["safe", "low_risk", "high_risk", "blocked"] = Field(
        ..., description="Risk classification based on overall_score thresholds"
    )
    categories: list[SafetyCategory] = Field(
        default_factory=list, description="Per-category safety scores"
    )
    flagged_issues: list[str] = Field(
        default_factory=list, description="Human-readable list of flagged concerns"
    )
    recommendation: str = Field("", description="Action recommendation (proceed / review / block)")
    eval_tokens_in: int = Field(0, description="Input tokens used for safety eval")
    eval_tokens_out: int = Field(0, description="Output tokens used for safety eval")
    eval_cost_usd: float = Field(0.0, description="Cost of safety evaluation in USD")
