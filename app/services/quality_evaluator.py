"""
Quality Evaluator — Video Script & Prompt Quality Assessment
Step 6 of the Pipeline: evaluates generated ad scripts for quality across
5 dimensions using Seed 1.8. Non-blocking: failure results in quality=null.
"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.models.quality_schemas import QualityDimension, QualityEvalResult
from app.models.schemas import AdScript
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(
    api_key=settings.ark_api_key,
    base_url=settings.ark_base_url,
)

QUALITY_DIMENSIONS = [
    "prompt_clarity",
    "brand_alignment",
    "creative_quality",
    "technical_precision",
    "platform_fit",
]

SYSTEM_PROMPT = """\
You are a creative quality evaluator for AI-generated video ad scripts.
Evaluate the provided ad script and video prompt for quality across these dimensions:
prompt_clarity, brand_alignment, creative_quality, technical_precision, platform_fit.

Score each dimension from 0.0 (poor) to 1.0 (excellent).
Return JSON with exactly these keys:

{
  "overall_score": 0.0,
  "dimensions": [
    {"name": "prompt_clarity", "score": 0.0, "explanation": "..."},
    {"name": "brand_alignment", "score": 0.0, "explanation": "..."},
    {"name": "creative_quality", "score": 0.0, "explanation": "..."},
    {"name": "technical_precision", "score": 0.0, "explanation": "..."},
    {"name": "platform_fit", "score": 0.0, "explanation": "..."}
  ],
  "suggestions": []
}

Rules:
- overall_score is the average of all dimension scores
- suggestions lists actionable improvements (empty if all excellent)
- Only return valid JSON, no markdown fences
"""


def _classify_grade(score: float) -> str:
    """Classify quality grade based on score."""
    if score >= 0.8:
        return "excellent"
    if score >= 0.6:
        return "good"
    if score >= 0.4:
        return "fair"
    return "poor"


def _calculate_eval_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate quality evaluation cost using Seed 1.8 pricing."""
    input_cost = (input_tokens / 1_000_000) * settings.cost_per_m_seed18_input
    output_cost = (output_tokens / 1_000_000) * settings.cost_per_m_seed18_output
    return round(input_cost + output_cost, 6)


@retry_with_backoff(max_retries=2, initial_delay=1.0)
async def evaluate_video_quality(
    script: AdScript,
    brief: str = "",
    platforms: list[str] | None = None,
) -> tuple[QualityEvalResult, int, int]:
    """
    Evaluate an ad script for quality using Seed 1.8.
    Returns (QualityEvalResult, input_tokens, output_tokens) for cost tracking.
    """
    platform_str = ", ".join(platforms) if platforms else "general"
    content = (
        f"Brief: {brief}\n"
        f"Target Platforms: {platform_str}\n"
        f"Ad Copy: {script.ad_copy}\n"
        f"Scene Description: {script.scene_description}\n"
        f"Video Prompt: {script.video_prompt}\n"
        f"Camera Direction: {script.camera_direction}"
    )

    response = await _client.chat.completions.create(
        model=settings.script_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=settings.quality_temperature,
        max_tokens=settings.quality_max_tokens,
    )

    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse quality eval output: %s", raw)
        data = {
            "overall_score": 0.5,
            "dimensions": [
                {
                    "name": dim,
                    "score": 0.5,
                    "explanation": "Parse error — defaulting to fair",
                }
                for dim in QUALITY_DIMENSIONS
            ],
            "suggestions": ["Quality evaluation encountered a parsing error"],
        }

    overall_score = float(data.get("overall_score", 0.5))
    grade = _classify_grade(overall_score)
    eval_cost = _calculate_eval_cost(input_tokens, output_tokens)

    dimensions = [
        QualityDimension(
            name=dim.get("name", "unknown"),
            score=float(dim.get("score", 0.5)),
            explanation=dim.get("explanation", ""),
        )
        for dim in data.get("dimensions", [])
    ]

    result = QualityEvalResult(
        overall_score=overall_score,
        grade=grade,
        dimensions=dimensions,
        suggestions=data.get("suggestions", []),
        eval_tokens_in=input_tokens,
        eval_tokens_out=output_tokens,
        eval_cost_usd=eval_cost,
    )

    return result, input_tokens, output_tokens
