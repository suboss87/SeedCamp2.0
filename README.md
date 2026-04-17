# SeedCamp

**Open-source reference architecture for AI video generation at scale.** Fork it, adapt it, ship it.

[![CI](https://github.com/suboss87/SeedCamp2.0/actions/workflows/ci.yml/badge.svg)](https://github.com/suboss87/SeedCamp2.0/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/) [![Seedance 2.0](https://img.shields.io/badge/Seedance-2.0-ff7a59)](https://seed.bytedance.com/en/seedance2_0) [![Deploy](https://img.shields.io/badge/deploy-7%20platforms-orange)](#deploy-anywhere)

> **April 2026:** [Seedance 2.0](https://seed.bytedance.com/en/seedance2_0) is now in public beta, ranked #2 on Artificial Analysis with native audio and 15s multi-shot. [Sora shuts down April 26.](docs/MIGRATE_FROM_SORA.md) SeedCamp ships with Seedance 2.0 model IDs and a migration path from Sora.

---

## What is SeedCamp?

SeedCamp is a production-ready Python codebase that solves the hard parts of building an AI video generation pipeline. It is not a managed service or a SaaS product. It is a reference architecture: a working system you can study, fork, and adapt for your own use case.

**The problem it solves:** Calling a video generation API once is easy. Calling it 10,000 times requires:

- Async polling with timeouts (the API is fire-and-forget)
- Retry with exponential backoff and `Retry-After` honoring
- Tiered model routing (premium model for your best 20%, fast model for the rest)
- Per-request cost tracking and budget enforcement
- Safety evaluation before generation (catch bad prompts before they burn credits)
- Concurrency control (semaphore-based, not "launch 500 tasks and pray")

Most teams spend 2-3 weeks building this from scratch. SeedCamp gives you a tested, documented starting point.

```python
from app.services.pipeline import run_pipeline
from app.models.schemas import SKUTier

result = await run_pipeline(
    sku_id="SUV-001",
    brief="Luxury SUV on mountain pass at golden hour, cinematic walkaround",
    sku_tier=SKUTier.hero,
)
print(result["task_id"], result["cost"].total_cost_usd)
```

---

## Who is this for?

**Use SeedCamp if:**

- You are an engineering team building a custom video generation pipeline
- You evaluated managed platforms (Shotstack, Oxolo, Creatify) but need more control
- You want to see how production-grade async AI pipelines are structured
- You need 100+ videos and want retry, routing, and cost tracking out of the box
- You are migrating from Sora and need a working alternative on Seedance 2.0

**Use something else if:**

- You need fewer than 50 videos. Just call the [ModelArk API](https://docs.byteplus.com/en/docs/ModelArk/1399008) directly.
- You want a managed service with a UI. Try [Shotstack](https://shotstack.io), [Oxolo](https://oxolo.com), or [Creatify](https://creatify.ai).
- You want multi-provider routing today. Try [Vercel AI Gateway](https://vercel.com/docs/ai-gateway/capabilities/video-generation). SeedCamp is BytePlus-native; provider abstraction is on the [v1.1 roadmap](https://github.com/suboss87/SeedCamp2.0/issues/1).
- You need template-based video (swap product images into a template). That is a different problem.

---

## The 5 patterns

Every pattern is extracted, tested, and documented. They transfer to any async AI workload, not just video.

| Pattern | What it does | File | Lines |
|---|---|---|---|
| **Tiered Model Routing** | Route hero items to Seedance 2.0, catalog items to 2.0 Fast | [`model_router.py`](app/services/model_router.py) | ~37 |
| **Async Task Pipeline** | Fire-and-forget video creation with polling, timeout, and SSE streaming | [`video_gen.py`](app/services/video_gen.py) | ~163 |
| **Cost Tracking** | Per-request token counting, per-tier attribution, Prometheus metrics | [`cost_tracker.py`](app/services/cost_tracker.py) | ~91 |
| **Batch Orchestration** | Semaphore-controlled concurrency with budget caps and error isolation | [`batch_generator.py`](app/services/batch_generator.py) | ~266 |
| **Retry with Backoff** | Exponential backoff, `Retry-After` headers, structured error classification | [`retry.py`](app/utils/retry.py) | ~210 |

Also included: safety evaluation (7-category content classifier with configurable block thresholds), quality gates (5-dimension scoring, non-blocking), a Streamlit dashboard, a FastAPI server with `/metrics` and `/health`, and deploy artifacts for 7 platforms.

---

## Quickstart

```bash
git clone https://github.com/suboss87/SeedCamp2.0.git && cd SeedCamp2.0
make install

# Try the full pipeline without an API key (dry-run simulates all API calls)
DRY_RUN=true make dev    # API on :8000, dashboard on :8501
```

When ready for real generation, [get an ARK_API_KEY](https://www.byteplus.com/en/product/modelark) and add it to `.env`.

```bash
python3 docs/examples/generate_single_video.py   # one video
python3 docs/examples/automotive_dealer.py       # 10 vehicles, tiered routing
python3 docs/examples/ecommerce_catalog.py       # 100 SKUs, batch with cost cap
```

---

## Architecture

```mermaid
graph LR
    A[Brief + tier] --> B[Script gen: Seed 1.8]
    B --> C[Safety eval: 7 categories]
    C -->|blocked| X[Reject]
    C -->|safe| D{Router}
    D -->|hero 20%| E[Seedance 2.0]
    D -->|catalog 80%| F[Seedance 2.0 Fast]
    E --> G[Quality eval: 5 dims]
    F --> G
    G --> H[Cost tracking + delivery]
```

Safety evaluation is **blocking**: if content scores above the threshold, generation is rejected before spending credits. Quality evaluation is **non-blocking**: scores are delivered alongside the video.

| Step | Technology |
|---|---|
| 1. Input | FastAPI + Streamlit dashboard |
| 2. Script generation | Seed 1.8 via ModelArk |
| 3. Safety classification | Seed 1.8, 7 categories with scores |
| 4. Model routing | Pure function, configurable per tier |
| 5. Video generation | Seedance 2.0 or 2.0 Fast, async polling |
| 6. Quality evaluation | Seed 1.8, 5-dimension scoring |
| 7. Cost accounting | In-memory (single worker) or Firestore |

---

## Adapt for your vertical

The tier system is a simple enum. Changing it takes three lines.

```python
# Automotive: certified pre-owned to premium, aged stock to fast
class VehicleTier(str, Enum):
    featured = "featured"      # routes to Seedance 2.0
    inventory = "inventory"    # routes to Seedance 2.0 Fast

# E-commerce: best sellers to premium, long tail to fast
class ProductTier(str, Enum):
    hero = "hero"              # routes to Seedance 2.0
    catalog = "catalog"        # routes to Seedance 2.0 Fast
```

| Vertical | Hero tier | Catalog tier | Scale |
|---|---|---|---|
| **Automotive** | Certified, new arrivals | Wholesale, aged stock | 300-500K vehicles |
| **E-commerce** | Top 20% revenue SKUs | Long-tail catalog | 1K-100K SKUs |
| **Ad creative** | Campaign hero spots | Social cutdowns | 100-10K assets |

---

## Migrating from Sora?

Sora shuts down April 26 (app) and September 24 (API). If you have a Sora integration, SeedCamp is a drop-in path to Seedance 2.0.

```python
# Before: Sora (deprecated)
response = openai.videos.generate(prompt=brief, model="sora-2")

# After: SeedCamp on Seedance 2.0
result = await run_pipeline(sku_id="x", brief=brief, sku_tier=SKUTier.hero)
```

Seedance 2.0 is roughly 10x cheaper per second than Sora 2 Pro, ranks higher on Artificial Analysis (#2 vs absent), and generates audio natively.

Full migration guide: [docs/MIGRATE_FROM_SORA.md](docs/MIGRATE_FROM_SORA.md)

---

## Deploy anywhere

| Platform | Guide | Setup |
|---|---|---|
| **Local** | `make dev` | No Docker needed |
| **Docker** | [`deploy/docker/`](deploy/docker/) | `make docker-up` |
| **GCP Cloud Run** | [`deploy/gcp/`](deploy/gcp/) | Terraform |
| **AWS ECS Fargate** | [`deploy/aws/`](deploy/aws/) | Terraform |
| **BytePlus VKE** | [`deploy/byteplus/`](deploy/byteplus/) | K8s manifests |
| **Railway** | [`deploy/railway/`](deploy/railway/) | One-click |
| **Render** | [`deploy/render/`](deploy/render/) | One-click |

Before deploying publicly, read the [Security Checklist](docs/QUICKSTART.md#security-checklist-read-before-going-public). Set `API_KEY`, restrict `CORS_ORIGINS`, and put the Streamlit dashboard behind auth.

---

## Links

- [Quick Start](docs/QUICKSTART.md) - Railway, Render, Docker in 30 minutes
- [Deployment Guide](docs/DEPLOYMENT.md) - All platforms, step by step
- [Migrating from Sora](docs/MIGRATE_FROM_SORA.md) - Code diffs, pricing, timeline
- [Market Research](docs/market-research.md) - Data behind the positioning
- [API Reference](http://localhost:8000/docs) - Swagger UI (run locally)
- [Contributing](.github/CONTRIBUTING.md) - Good first issues labeled
- [Security](.github/SECURITY.md) - Vulnerability reporting

---

## Honest trade-offs

SeedCamp is a reference architecture, not a managed service. Know what you are getting:

- **BytePlus ModelArk only, today.** Provider abstraction is planned for v1.1. Track it in [issue #1](https://github.com/suboss87/SeedCamp2.0/issues/1). Until then, this only works with Seedance models.
- **Cost tracker is in-memory.** Running with multiple workers means `/api/cost-summary` returns partial data. Use a single worker or back it with Firestore. A startup warning fires when this is detected.
- **Tests are mocked.** The 112-test suite verifies orchestration logic, not real API behavior. Run the examples with a real `ARK_API_KEY` for end-to-end validation.
- **Safety evaluation uses an LLM as judge.** False positives happen. Thresholds are configurable via `SAFETY_THRESHOLD_*` environment variables.
- **Seedance 2.0 API is in public beta.** Rate limits are currently 2 QPS and 3 concurrent tasks per account. This will improve but affects throughput today.

---

Built by [Subash Natarajan](https://www.linkedin.com/in/subashn/) | Powered by [BytePlus ModelArk](https://www.byteplus.com/en/product/modelark) | MIT licensed
