"""
Safety Evaluator -- Responsible AI Content Safety Layer
Step 2.5 of the Pipeline: evaluates generated ad scripts for safety concerns
before routing to video generation. Uses Seed 1.8 as a safety classifier.
"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.models.safety_schemas import SafetyCategory, SafetyEvalResult
from app.models.schemas import AdScript
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Client created at import time -- API key is captured once. This module is only
# imported when dry_run=False, so the key is always valid at import time.
_client = AsyncOpenAI(
    api_key=settings.ark_api_key,
    base_url=settings.ark_base_url,
)

SAFETY_CATEGORIES = [
    "bias",
    "stereotypes",
    "violence",
    "sexual_content",
    "hate_speech",
    "cultural_insensitivity",
    "brand_safety",
]

SYSTEM_PROMPT = """\
You are a Responsible AI content safety evaluator for advertising.
Evaluate the provided ad script for safety concerns across these categories:
bias, stereotypes, violence, sexual_content, hate_speech, cultural_insensitivity, brand_safety.

Score each category from 0.0 (safe) to 1.0 (high risk).
Return JSON with exactly these keys:

{
  "overall_score": 0.0,
  "categories": [
    {"name": "bias", "score": 0.0, "explanation": "..."},
    {"name": "stereotypes", "score": 0.0, "explanation": "..."},
    {"name": "violence", "score": 0.0, "explanation": "..."},
    {"name": "sexual_content", "score": 0.0, "explanation": "..."},
    {"name": "hate_speech", "score": 0.0, "explanation": "..."},
    {"name": "cultural_insensitivity", "score": 0.0, "explanation": "..."},
    {"name": "brand_safety", "score": 0.0, "explanation": "..."}
  ],
  "flagged_issues": [],
  "recommendation": "proceed"
}

Rules:
- overall_score is the maximum of all category scores
- flagged_issues lists human-readable concerns (empty if all safe)
- recommendation is one of: "proceed", "review", "block"
- Only return valid JSON, no markdown fences
"""


def _classify_risk(
    score: float,
) -> str:
    """Classify risk level based on score and configured thresholds."""
    if score >= settings.safety_threshold_block:
        return "blocked"
    if score >= settings.safety_threshold_high_risk:
        return "high_risk"
    if score >= settings.safety_threshold_flag:
        return "low_risk"
    return "safe"


def _calculate_eval_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate safety evaluation cost using Seed 1.8 pricing."""
    input_cost = (input_tokens / 1_000_000) * settings.cost_per_m_seed18_input
    output_cost = (output_tokens / 1_000_000) * settings.cost_per_m_seed18_output
    return round(input_cost + output_cost, 6)


@retry_with_backoff(max_retries=2, initial_delay=1.0)
async def evaluate_content_safety(
    script: AdScript,
) -> tuple[SafetyEvalResult, int, int]:
    """
    Evaluate an ad script for content safety using Seed 1.8.
    Returns (SafetyEvalResult, input_tokens, output_tokens) for cost tracking.

    Automatically retries on transient failures (network, 5xx, rate limits).
    """
    content = (
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
        temperature=settings.safety_temperature,
        max_tokens=settings.safety_max_tokens,
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
        logger.error("Failed to parse safety eval output: %s", raw)
        data = {
            "overall_score": 0.0,
            "categories": [
                {
                    "name": cat,
                    "score": 0.0,
                    "explanation": "Parse error -- defaulting to safe",
                }
                for cat in SAFETY_CATEGORIES
            ],
            "flagged_issues": [],
            "recommendation": "proceed",
        }

    overall_score = float(data.get("overall_score", 0.0))
    risk_level = _classify_risk(overall_score)
    eval_cost = _calculate_eval_cost(input_tokens, output_tokens)

    categories = [
        SafetyCategory(
            name=cat.get("name", "unknown"),
            score=float(cat.get("score", 0.0)),
            explanation=cat.get("explanation", ""),
        )
        for cat in data.get("categories", [])
    ]

    result = SafetyEvalResult(
        overall_score=overall_score,
        risk_level=risk_level,
        categories=categories,
        flagged_issues=data.get("flagged_issues", []),
        recommendation=data.get("recommendation", "proceed"),
        eval_tokens_in=input_tokens,
        eval_tokens_out=output_tokens,
        eval_cost_usd=eval_cost,
    )

    return result, input_tokens, output_tokens
