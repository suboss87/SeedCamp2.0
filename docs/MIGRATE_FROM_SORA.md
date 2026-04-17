# Migrating from Sora to SeedCamp (Seedance 2.0)

OpenAI announced the Sora shutdown in March 2026:
- **App/web** closes **April 26, 2026**
- **API** closes **September 24, 2026**
- Export your data before the deadlines -- [OpenAI help article](https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation)

This guide walks you through migrating a Sora integration to SeedCamp on Seedance 2.0.

---

## Why Seedance 2.0?

| Dimension | Sora 2 Pro | Seedance 2.0 (via SeedCamp) |
|---|---|---|
| **Quality ranking** | Not on Artificial Analysis leaderboard | #2 T2V, #2 I2V (April 2026) |
| **Cost (per 10s video)** | ~$5.00 (Pro 1080p) | ~$0.04–0.08 (Fast 720p) |
| **Native audio** | Added late, basic | Joint audio-video gen, lip-sync, foley |
| **Max duration** | 20s (single shot) | 15s (multi-shot with scene control) |
| **Resolution** | 1080p | Up to 1080p (Standard), 720p (Fast) |
| **API status** | Shutting down Sep 2026 | Public beta, actively developed |
| **Retry / orchestration** | DIY | Built into SeedCamp |
| **Batch generation** | DIY | Built into SeedCamp |
| **Cost tracking** | None | Per-request, per-tier |
| **Safety gates** | OpenAI moderation (opaque) | 7-category classifier, configurable thresholds |

---

## Step 1: Get a BytePlus ModelArk API key

1. Sign up at [byteplus.com/en/product/modelark](https://www.byteplus.com/en/product/modelark)
2. Create an API key in the console
3. You get **20 free Seedance 2.0 Fast invocations/month** to test

---

## Step 2: Install SeedCamp

```bash
git clone https://github.com/suboss87/SeedCamp2.0.git && cd SeedCamp2.0
make install
cp .env.example .env
# Edit .env → set ARK_API_KEY=<your-key>
```

---

## Step 3: Replace Sora API calls

**Before (Sora):**
```python
import openai

client = openai.OpenAI()
response = client.videos.generate(
    model="sora-2",
    prompt="Product showcase on white background, slow rotation",
    duration=10,
    resolution="1080p",
)
video_url = response.url
```

**After (SeedCamp):**
```python
from app.services.pipeline import run_pipeline
from app.models.schemas import SKUTier

result = await run_pipeline(
    sku_id="product-001",
    brief="Product showcase on white background, slow rotation",
    sku_tier=SKUTier.hero,  # or SKUTier.catalog for cost-optimized
)
# result is a dict with keys: script, model_id, task_id, cost, safety, quality
task_id = result["task_id"]        # poll /api/status/{task_id} for the video URL
cost = result["cost"].total_cost_usd
safety = result["safety"].risk_level if result["safety"] else "safe"
```

**Via HTTP API:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "product-001", "brief": "Product showcase, slow rotation", "sku_tier": "hero"}'
```

---

## Step 4: Map your Sora prompts to tiers

SeedCamp routes requests to different models based on business value:

| Your content | Sora model | SeedCamp tier | Seedance model | Cost |
|---|---|---|---|---|
| Hero products, hero ads | sora-2 (Pro) | `hero` | Seedance 2.0 Standard | ~$0.04/video |
| Bulk catalog, variants | sora-2 (standard) | `catalog` | Seedance 2.0 Fast | ~$0.03/video |

If you were paying $5/video on Sora Pro, you're now paying ~$0.04. At 1,000 videos/month, that's **$5,000 → $40**.

---

## Step 5: Test in dry-run mode

Before spending real credits:

```bash
DRY_RUN=true make dev
# Open http://localhost:8501 → paste a Sora prompt → verify the pipeline works
```

---

## Step 6: Batch migrate existing prompts

If you have a CSV of Sora prompts:

```python
# Convert sora-prompts.csv → SeedCamp batch
# Note: run_batch() is async -- wrap with asyncio.run() for scripts.
import asyncio
import csv
import uuid

from app.models.campaign_schemas import Campaign, Product
from app.services.batch_generator import run_batch

products = []
with open("sora-prompts.csv") as f:
    for row in csv.DictReader(f):
        products.append(Product(
            id=uuid.uuid4().hex[:12],
            campaign_id="sora-migration",
            sku_id=row["id"],
            product_name=row.get("name", row["id"]),
            description=row["prompt"],
            sku_tier="hero" if row.get("priority") == "high" else "catalog",
        ))

campaign = Campaign(
    id="sora-migration",
    name="Sora Migration",
    theme="Migrated Sora prompts",
    total_products=len(products),
)
asyncio.run(run_batch(campaign=campaign, products=products))
```

---

## Key differences to know

| Sora behavior | SeedCamp behavior |
|---|---|
| Sync response (blocks until done) | Async: returns task_id, poll or use SSE stream |
| Single model, single price | Two tiers, routed by `sku_tier` |
| OpenAI moderation (binary pass/fail) | 7-category safety eval with configurable thresholds |
| No cost tracking | Per-request cost breakdown |
| No retry logic | Exponential backoff with Retry-After |
| No batch mode | Semaphore-controlled batch with budget caps |

---

## Timeline

| Date | What happens | Action |
|---|---|---|
| Now | Sora app still works | Start migration, test in dry-run |
| **April 26, 2026** | Sora app/web shuts down | Export all generated videos |
| May–Aug 2026 | Sora API still works (deprecated) | Run Sora and SeedCamp in parallel, validate |
| **September 24, 2026** | Sora API shuts down | Full cutover to SeedCamp |

---

## Need help?

- [Open an issue](https://github.com/suboss87/SeedCamp2.0/issues) with the `migration` label
- Check [docs/QUICKSTART.md](QUICKSTART.md) for deployment options
- Join the discussion in [GitHub Discussions](https://github.com/suboss87/SeedCamp2.0/discussions)
