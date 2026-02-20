# AdCamp: Reference Architecture for Cost-Optimized AI Content Generation

[![BytePlus ModelArk](https://img.shields.io/badge/Powered%20by-BytePlus%20ModelArk-blue)](https://www.byteplus.com/en/product/modelark)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen)]()

> **Built by [Subash Natarajan](https://www.linkedin.com/in/subashn/)** — Production-ready architecture patterns for AI generation at scale.

---

## Why This Exists

Every organization scaling AI content generation hits the same problem: **not every request deserves your most expensive model.** A luxury property listing needs cinematic video quality. A standard rental listing needs good-enough video, fast and cheap. A flagship course needs premium voiceover. A quick tutorial needs functional TTS.

Yet most AI pipelines treat every request identically — same model, same cost, same latency. At scale (thousands of items across multiple formats), this becomes a **cost and speed bottleneck**.

**AdCamp solves this with tiered model routing** — automatically directing each workload to the right AI model based on its business value, while providing the async pipeline infrastructure, cost tracking, batch orchestration, and resilience patterns needed for production deployment.

Implemented as a **video generation pipeline** on BytePlus ModelArk, but the architecture patterns apply to any AI content workload.

## Architecture

<img width="1166" alt="AdCamp Pipeline Architecture" src="https://github.com/user-attachments/assets/b94bff18-f54d-4962-858e-b4d866afa79a" />

### Five Reusable Patterns

This reference architecture demonstrates five production patterns that transfer to any AI generation pipeline:

#### 1. Tiered Model Routing
Route workloads to different models based on business value — premium quality for high-value items, cost-optimized for the long tail.

```python
# app/services/model_router.py — 29 lines, pure function
_ROUTES = {
    SKUTier.hero:    lambda: (settings.video_model_pro,  settings.cost_per_m_seedance_pro),
    SKUTier.catalog: lambda: (settings.video_model_fast, settings.cost_per_m_seedance_fast),
}
```

**Swap point**: Replace `SKUTier` with your own tier logic (customer segment, content priority, SLA level). Replace model IDs with any ModelArk model.

#### 2. Async Task Pipeline
Submit long-running AI jobs, poll for completion, handle success/failure/timeout — the universal pattern for any AI API that doesn't return results immediately.

```
POST /generate → task_id → GET /status/{task_id} → poll → result
```

**Swap point**: Replace `video_gen.create_video_task()` with any async AI API call.

#### 3. Token-Aware Cost Tracking
Track costs per request in real-time — tokens consumed, model used, cost per tier. Essential for any metered AI API (ModelArk, OpenAI, Anthropic, Stability).

```python
# Every pipeline run returns: {cost: CostBreakdown, model_id, in_tokens, out_tokens}
```

**Swap point**: Plug in your own token pricing from any AI provider.

#### 4. Batch Orchestration
Process thousands of items concurrently with semaphore-controlled parallelism, progress tracking, and partial failure handling.

```python
# app/services/batch_generator.py — asyncio.Semaphore(concurrency)
```

**Swap point**: Replace the video generation call with any AI workload.

#### 5. Resilient API Integration
Exponential backoff with rate-limit honoring (`Retry-After` header), error classification (retryable vs fatal), and circuit-breaking for non-recoverable errors.

```python
@retry_with_backoff(max_retries=3, initial_delay=2.0)
async def create_video_task(...):
```

**Swap point**: Wrap any external API call with `@retry_with_backoff`.

---

## Cross-Industry Applications

The tiered routing pattern applies wherever you have inventory with varying business value:

| Industry | Premium Tier (best model) | Standard Tier (fast model) | Scale |
|---|---|---|---|
| **E-commerce / D2C** | Hero products (top 20% revenue) | Catalog inventory (long tail) | 1K-100K SKUs |
| **Real estate** | Luxury listings ($1M+ properties) | Standard rental/sale listings | 500-50K listings |
| **Automotive** | Featured/certified vehicles | Bulk dealer inventory | 1K-500K vehicles |
| **Travel & hospitality** | Premium destinations, suites | Standard hotel rooms | 10K-1M listings |
| **Education** | Flagship courses, programs | Course previews, teasers | 100-10K courses |
| **Media & entertainment** | Campaign hero spots | Social media variants, cutdowns | 100-10K assets |
| **Food & beverage** | Signature/seasonal menu items | Standard menu catalog | 50-5K items |
| **Fashion & apparel** | Runway/editorial pieces | Product catalog shots | 1K-100K SKUs |
| **B2B SaaS** | Enterprise client demos | Feature walkthroughs | 50-500 demos |

**The pattern is the same**: identify your high-value items, route them to your best model, and route everything else to a faster, cheaper alternative.

---

## Implementation: Video Generation on ModelArk

This reference architecture is implemented as a complete video generation pipeline using BytePlus ModelArk's Seed and Seedance models.

### Pipeline Flow

| Step | Component | What It Does | Model | Cost (5s, 720p, audio) |
|------|-----------|-------------|-------|------|
| 1 | **Input** | Campaign brief + product image + tier | — | — |
| 2 | **Script Gen** | AI generates ad copy + video prompt | Seed 1.8 | ~$0.002 |
| 3 | **Smart Router** | Routes premium vs standard tier | — | — |
| 4 | **Video Gen** | Async video generation with polling | Seedance Pro/Fast | $0.29-0.49 |
| 5 | **Output** | Platform-ready MP4 (TikTok, IG, YouTube) | — | — |

### Model Economics

```
Premium Tier  ──▶  Seedance 1.5 Pro     ($1.20/M tokens) ──▶  ~$0.49/video
Standard Tier ──▶  Seedance 1.0 Pro Fast ($0.70/M tokens) ──▶  ~$0.29/video

Blended (20/80 split): ~$0.33/video
```

> Token formula: `(Width x Height x FPS x Duration) / 1024 x Coefficient` — [BytePlus pricing docs](https://docs.byteplus.com/en/docs/ModelArk/1544106)

### Cost at Scale

| Scale | Items | Videos/Year | Annual Cost | vs Manual Production |
|-------|-------|-------------|-------------|---------------------|
| Small | 500 | ~6,900 | ~$2,277 | 99.5% savings |
| Medium | 2,500 | ~34,500 | ~$11,385 | 99.3% savings |
| Large | 10,000 | ~138,000 | ~$45,540 | 99.1% savings |

*3 platforms x 30% monthly refresh x 12 months + 25% buffer. Enterprise pricing from BytePlus can reduce costs further.*

---

## Quick Start

```bash
# Clone
git clone https://github.com/suboss87/adcamp.git
cd adcamp

# Install
make install

# Configure — add your BytePlus ModelArk API key
cp .env.example .env
# Edit .env: ARK_API_KEY=your_key_here

# Run (API on :8000, Dashboard on :8501)
make dev
```

**Generate your first video:**
```bash
python3 examples/generate_single_video.py
```

**Interactive API docs:** http://localhost:8000/docs

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI Models** | [BytePlus ModelArk](https://www.byteplus.com/en/product/modelark) | Seed 1.8 (scripts), Seedance Pro/Fast (video) |
| **Backend** | FastAPI + async/await | API server, SSE streaming, async polling |
| **Dashboard** | Streamlit | Campaign management, A/B comparison, analytics |
| **Persistence** | Google Firestore | Campaign and product data |
| **Resilience** | Custom `@retry_with_backoff` | Exponential backoff, rate-limit honoring |
| **Deployment** | Docker, GCP Cloud Run, Terraform | Multi-platform with IaC |
| **Monitoring** | Prometheus-compatible `/metrics` | Cost tracking, request counts, health checks |

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/generate` | POST | Full pipeline — returns task_id for polling |
| `/api/generate-stream` | POST | Full pipeline with SSE live progress |
| `/api/status/{task_id}` | GET | Poll generation status |
| `/api/wait/{task_id}` | GET | Block until ready |
| `/api/campaigns/` | POST | Create a campaign |
| `/api/campaigns/{id}/products/csv` | POST | Upload product catalog (CSV) |
| `/api/campaigns/{id}/generate` | POST | Start batch generation |
| `/api/cost-summary` | GET | Aggregate cost tracking |
| `/health` | GET | Health + model config |
| `/metrics` | GET | Prometheus text format |

## Deployment

| Platform | Setup | Best For | Guide |
|----------|-------|----------|-------|
| **Docker Compose** | 5 min | Local development | [deploy/docker/](deploy/docker/) |
| **GCP Cloud Run** | 20 min | Production (serverless) | [deploy/gcp/](deploy/gcp/) |
| **Terraform (GCP)** | 30 min | Infrastructure as Code | [deploy/gcp/terraform/](deploy/gcp/terraform/) |
| **AWS ECS** | 30 min | AWS ecosystem | [deploy/aws/](deploy/aws/) |
| **Kubernetes** | 45 min | Full control | [deploy/byteplus/](deploy/byteplus/) |

## Project Structure

```
adcamp/
├── app/
│   ├── main.py                 # FastAPI orchestrator
│   ├── config.py               # Pydantic Settings (.env)
│   ├── models/                 # Pydantic schemas
│   ├── services/
│   │   ├── model_router.py     # ⭐ Tiered routing logic (Pattern 1)
│   │   ├── video_gen.py        # ⭐ Async task + polling (Pattern 2)
│   │   ├── cost_tracker.py     # ⭐ Token-aware costing (Pattern 3)
│   │   ├── batch_generator.py  # ⭐ Semaphore concurrency (Pattern 4)
│   │   ├── pipeline.py         # Orchestrates patterns 1-3
│   │   ├── script_writer.py    # Seed 1.8 integration (OpenAI-compatible)
│   │   ├── brief_generator.py  # AI brief generation per product
│   │   ├── csv_parser.py       # Product catalog CSV import
│   │   └── firestore_client.py # Firestore persistence
│   ├── routes/
│   │   └── campaigns.py        # Campaign CRUD + batch endpoints
│   └── utils/
│       └── retry.py            # ⭐ @retry_with_backoff (Pattern 5)
├── dashboard/                  # Streamlit UI (tabs, A/B comparison)
├── deploy/                     # Docker, GCP, AWS, K8s, monitoring
├── examples/                   # Runnable scripts
├── tests/                      # Unit tests (13 passing)
└── docs/                       # Architecture docs + guides
```

## Adapting for Your Use Case

To use this architecture with a different AI workload:

1. **Define your tiers** — Edit `app/models/schemas.py:SKUTier` with your business tiers
2. **Update the router** — Edit `app/services/model_router.py` to map tiers to your ModelArk models
3. **Replace the generation step** — Swap `video_gen.py` with your AI API (image gen, audio, etc.)
4. **Adjust cost constants** — Update `app/config.py` with your model's token pricing
5. **Customize the dashboard** — Edit `dashboard/sections.py` for your domain

The pipeline orchestration, retry logic, batch processing, cost tracking, and API layer remain unchanged.

## Testing

```bash
make test                                    # All tests with coverage
pytest tests/unit/test_model_router.py -v    # Router tests only
pytest tests/unit/test_csv_parser.py -v      # CSV parser tests only
```

## Documentation

- **[DEPLOY.md](DEPLOY.md)** — GCP Cloud Run deployment guide
- **[AGENTS.md](AGENTS.md)** — Full architecture reference for AI coding agents
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Contribution guidelines
- **[examples/](examples/)** — Runnable Python scripts
- **API Docs** — http://localhost:8000/docs (Swagger) / http://localhost:8000/redoc

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
make install    # Setup environment
make test       # Run tests (13 passing)
make lint       # Check code style
```

## License

MIT License — see [LICENSE](LICENSE).

---

**Built by [Subash Natarajan](https://www.linkedin.com/in/subashn/)** | Powered by [BytePlus ModelArk](https://www.byteplus.com/en/product/modelark) | [View Source](https://github.com/suboss87/adcamp)
