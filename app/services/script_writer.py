"""
Script Writer — Seed 1.8
Step 2 of the D2C Pipeline: converts campaign brief into
ad copy, scene descriptions, and optimized Seedance video prompts.
"""
import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.models.schemas import AdScript
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(
    api_key=settings.ark_api_key,
    base_url=settings.ark_base_url,
)

SYSTEM_PROMPT = """\
You are an expert D2C video ad creative director.
Given a product campaign brief, produce JSON with exactly these keys:

{
  "ad_copy": "A punchy 1-2 sentence ad headline/copy for the product",
  "scene_description": "2-3 sentence visual scene description (setting, lighting, mood, props)",
  "video_prompt": "A detailed Seedance video generation prompt (2-4 sentences). Include: subject in motion, lighting style, mood, specific camera movement (e.g. slow dolly in, tracking shot, orbit). Be cinematic and specific.",
  "camera_direction": "One concise line describing the primary camera movement and style."
}

Rules:
- Write all prompts in English
- video_prompt must describe MOTION (product rotating, liquid pouring, fabric flowing, etc.)
- Include lighting direction (golden hour, studio rim light, neon glow, etc.)
- Keep video_prompt under 150 words
- Only return valid JSON, no markdown fences
"""


@retry_with_backoff(max_retries=3, initial_delay=1.0)
async def generate_script(brief: str) -> tuple[AdScript, int, int]:
    """
    Generate ad script from campaign brief using Seed 1.8.
    Returns (AdScript, input_tokens, output_tokens) for cost tracking.
    
    Automatically retries on transient failures (network, 5xx, rate limits).
    """
    response = await _client.chat.completions.create(
        model=settings.script_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Campaign brief: {brief}"},
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    # Extract token usage
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse script output: %s", raw)
        data = {
            "ad_copy": brief,
            "scene_description": brief,
            "video_prompt": brief,
            "camera_direction": "Slow zoom in on the product",
        }

    return AdScript(**data), input_tokens, output_tokens
