"""
Auto-Brief Engine -- Core Value Proposition
Stage A of the two-stage approach:
  campaign_theme + product_data → optimized brief → (existing script_writer → AdScript)

Generates a tailored 2-4 sentence advertising brief for each product
by combining campaign-level theme with product-specific attributes.
Uses the same Seed 1.8 model via OpenAI SDK.
"""

import logging

from openai import AsyncOpenAI

from app.config import settings
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Client created at import time -- API key is captured once. This module is only
# imported when dry_run=False, so the key is always valid at import time.
_client = AsyncOpenAI(
    api_key=settings.ark_api_key,
    base_url=settings.ark_base_url,
)

SYSTEM_PROMPT = """\
You are an expert advertising creative director. Given a campaign theme \
and product details, write a focused advertising brief (2-4 sentences) that:

1. Captures the campaign mood/theme
2. Highlights the product's key selling points
3. Suggests a visual direction (setting, lighting, motion)
4. Matches the product's tier (hero = premium/cinematic, catalog = punchy/efficient)

Write ONLY the brief text -- no labels, no JSON, no markdown. Just the brief.
Keep it under 100 words. Be specific and visual.
"""


@retry_with_backoff(max_retries=3, initial_delay=1.0)
async def generate_brief(
    campaign_theme: str,
    product_name: str,
    description: str,
    sku_tier: str = "catalog",
    category: str = None,
) -> tuple[str, int, int]:
    """Generate an optimized advertising brief for a single product.

    Returns (brief_text, input_tokens, output_tokens) for cost tracking.
    """
    user_content = f"""Campaign theme: {campaign_theme}

Product: {product_name}
Description: {description}
Tier: {sku_tier} ({'premium cinematic quality' if sku_tier == 'hero' else 'cost-optimized, punchy'})"""

    if category:
        user_content += f"\nCategory: {category}"

    response = await _client.chat.completions.create(
        model=settings.script_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=settings.brief_temperature,
        max_tokens=settings.brief_max_tokens,
    )

    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0

    brief = response.choices[0].message.content.strip()
    logger.info(
        "Generated brief for %s (%d in / %d out tokens)",
        product_name,
        input_tokens,
        output_tokens,
    )

    return brief, input_tokens, output_tokens
