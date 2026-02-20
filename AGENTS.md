# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**AdCamp** is a reference architecture for cost-optimized AI video generation at scale, built on BytePlus ModelArk APIs. It generates platform-optimized videos with intelligent cost optimization through smart model routing — applicable across e-commerce, real estate, automotive, media, and any industry with inventory at varying business value.

### Key Architecture Concept: Smart Model Routing

The pipeline's core differentiator is **automatic tier-based routing**:
- **Hero SKUs** (top 20% products) → `Seedance 1.5 Pro` ($1.20/M tokens, premium quality)
- **Catalog SKUs** (80% inventory) → `Seedance 1.0 Pro Fast` ($0.70/M tokens, cost-optimized)

This achieves **~$0.09/video** blended cost (20/80 premium/standard split), enabling 34,500+ videos/year for ~$3,105.

### Pipeline Flow (5 Steps)

1. **Input**: Campaign brief + optional product image + SKU tier
2. **Script Generation**: `Seed 1.8` generates ad copy, scene description, and video prompt (~5s, ~$0.001)
3. **Smart Router**: Routes to appropriate Seedance model based on SKU tier
4. **Video Generation**: Async task creation via ModelArk API (~30s, $0.08-0.13)
5. **Output**: Platform-ready MP4 URLs + cost breakdown

## Development Commands

### Quick Start
```bash
make install    # Setup Python venv, install dependencies
make dev        # Run FastAPI (8000) + Streamlit dashboard (8501)
```

### Testing
```bash
make test       # Run pytest with coverage
pytest tests/unit/test_model_router.py -v    # Run specific test file
pytest -k "test_hero" -v                     # Run tests matching pattern
```

### Code Quality
```bash
make lint       # Run ruff + black checks
black app/ dashboard/    # Format code
ruff check app/ --fix    # Auto-fix linting issues
```

### Docker
```bash
make docker-build       # Build image (multi-stage)
make docker-up          # Start services via docker-compose
make docker-down        # Stop services
```

### Monitoring (Prometheus + Grafana)
```bash
cd deploy/monitoring
docker-compose up -d    # Start monitoring stack
docker-compose ps       # Check status
docker-compose down     # Stop monitoring stack

# Access:
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
# - AlertManager: http://localhost:9093
```

### Deployment

#### GCP Cloud Run
```bash
# Using Make (requires GCP_PROJECT_ID env var)
export GCP_PROJECT_ID=your-gcp-project-id
make deploy-gcp

# Build dashboard separately
gcloud builds submit --config=cloudbuild-dashboard.yaml . --project=your-gcp-project-id

# Check deployment logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --project=your-gcp-project-id

# Or use Terraform
cd deploy/gcp/terraform
terraform init
terraform apply
```

#### AWS ECS Fargate
```bash
# Using Terraform (recommended)
cd deploy/aws/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your API key and settings
terraform init
terraform plan
terraform apply

# View ECS services
aws ecs list-services --cluster adcamp-cluster --region ap-southeast-1

# View logs
aws logs tail /ecs/adcamp-api --follow --region ap-southeast-1
```

## Architecture & Code Structure

### Service Layer (`app/services/`)

**Critical Design Pattern**: All services implement async/await and use `@retry_with_backoff` decorator for resilience.

1. **`script_writer.py`** - Seed 1.8 integration
   - Uses OpenAI client (ModelArk is OpenAI-compatible)
   - Returns `(AdScript, input_tokens, output_tokens)` for cost tracking
   - System prompt enforces JSON output with motion-focused video prompts

2. **`model_router.py`** - Smart routing logic
   - Pure function: `route(sku_tier) -> (model_id, cost_per_m)`
   - Decision point: `SKUTier.hero` vs `SKUTier.catalog`
   - Returns both model ID and cost for downstream tracking

3. **`video_gen.py`** - Seedance video generation
   - **`create_video_task()`**: POST to `/contents/generations/tasks`, returns `task_id`
   - **`get_video_status()`**: GET task status, parses `succeeded`/`failed`/`running`
   - **`wait_for_video()`**: Polls until completion (timeout: 300s, interval: 5s)
   - **Image requirement**: Min 300px height (ModelArk enforces this)

4. **`cost_tracker.py`** - Cost calculation
   - Combines script tokens (Seed 1.8) + estimated video tokens
   - Returns `CostSummary` with per-component breakdown

### Retry Logic (`app/utils/retry.py`)

**Critical for production**: All ModelArk API calls wrapped in `@retry_with_backoff`.

- **Retryable errors**: Network failures, 5xx, 429 (rate limits)
- **Non-retryable**: 4xx (except 429), invalid API keys, image validation errors
- **Honors `Retry-After` header** for rate limit recovery
- **Custom exceptions**: `InvalidAPIKeyError`, `RateLimitError`, `QuotaExceededError`

### API Endpoints (`app/main.py`)

- **`POST /api/generate`**: Full pipeline (steps 1-4), returns immediately with `task_id`
- **`POST /api/generate-stream`**: SSE streaming endpoint with live progress updates (NEW)
- **`GET /api/status/{task_id}`**: Poll video generation status
- **`GET /api/wait/{task_id}`**: Blocking call (waits for completion)
- **`GET /health`**: Health check with model config + metrics
- **`GET /metrics`**: Prometheus text format
- **`GET /health/detailed`**: Extended health with dependency status

**SSE Stream Format** (`/api/generate-stream`):
- Streams JSON events via Server-Sent Events
- Event format: `data: {"step": 1-5, "status": "running|complete|failed", "message": "...", "progress": 0-100, "data": {...}}`
- Steps: 1) Initialize → 2) Script Gen → 3) Model Routing → 4) Task Creation → 5) Video Generation
- Final event includes video_url, cost breakdown, and script

### Environment Configuration (`app/config.py`)

Uses Pydantic Settings for type-safe config:

```python
ARK_API_KEY           # Required: BytePlus ModelArk API key
ARK_BASE_URL          # Default: https://ark.ap-southeast.bytepluses.com/api/v3
script_model          # Default: seed-1-8-251228
video_model_pro       # Default: seedance-1-5-pro-251215 (Hero)
video_model_fast      # Default: seedance-1-0-pro-fast-251015 (Catalog)
```

### Monitoring (`app/monitoring.py`)

In-memory metrics store (Prometheus-compatible):
- **Counters**: `videos_generated_total`, `videos_failed_total`, `hero_videos`, `catalog_videos`
- **Gauges**: `script_generation_avg_seconds`, `video_generation_avg_seconds`, `total_cost_usd`
- **Histogram**: Duration tracking for script/video generation

Metrics are **not persisted** across restarts (extend to Redis/Prometheus for production).

## Deployment Architecture

### Platform Organization (`deploy/`)

- **`deploy/docker/`**: Dockerfile (API), docker-compose.yml, Dockerfile.dashboard (Streamlit)
- **`deploy/gcp/`**: Cloud Run configs, Terraform templates, deployment scripts
- **`deploy/aws/`**: ECS Fargate + Terraform (VPC, ALB, Secrets Manager)
- **`deploy/byteplus/`**: VKE Kubernetes manifests (namespace, deployment, service, ingress)
- **`deploy/kubernetes/`**: Generic K8s with Kustomize (base + overlays for dev/staging/prod)
- **`deploy/monitoring/`**: Prometheus + Grafana stack with pre-configured dashboards and alerts

### Docker Image Details

**Multi-stage build** (`deploy/docker/Dockerfile`):
1. **Builder stage**: Compile Python dependencies
2. **Runtime stage**: Copy deps + app code
3. **Key**: Uses `ENV PORT=${PORT}` for Cloud Run compatibility (defaults to 8000, Cloud Run overrides to 8080)
4. **CMD**: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`

### Current Deployment

- **Project**: `your-gcp-project-id` (GCP)
- **API**: https://adcamp-api-qhfkhbdd4a-as.a.run.app
- **Dashboard**: https://adcamp-dashboard-qhfkhbdd4a-as.a.run.app
- **Secret**: `adcamp-ark-api-key` in GCP Secret Manager
- **Images**: `gcr.io/your-gcp-project-id/adcamp:latest`, `gcr.io/your-gcp-project-id/adcamp-dashboard:latest`
- **Latest Features**: SSE streaming, image upload, BytePlus branding

## Common Patterns & Conventions

### Error Handling

1. **Always use `@retry_with_backoff`** for external API calls
2. **Parse ModelArk errors** with `parse_modelark_error()` for user-friendly messages
3. **Log errors with context**: Include SKU ID, task ID, model used
4. **Return detailed responses**: Include error message in API response, not just HTTP status

### Async Programming

- **All services are async** (script_writer, video_gen)
- **Use `httpx.AsyncClient`** for HTTP calls (not `requests`)
- **Use `asyncio.sleep()`** for polling delays
- **FastAPI endpoints** should be `async def` when calling services

### Cost Tracking

- **Track tokens at every step**: Script input/output, video tokens
- **Estimate video tokens** from duration + resolution (actual from API when available)
- **Store per-tier costs**: Separate hero vs catalog in metrics
- **Include cost in responses**: Users should always see cost breakdown

### Image Validation

**Critical**: ModelArk requires images ≥300px height. Validate before sending to API to avoid cryptic 400 errors.

### Testing Against Real API

- **Use `.env` file** for local API key (never commit)
- **Test with catalog tier first** (cheaper for development)
- **Test without images initially** (simplifies debugging)
- **Monitor costs**: Each test video costs $0.08-0.13

## Security & Secrets

- **API keys**: Stored in GCP Secret Manager (prod), `.env` (local)
- **Never commit** `.env`, API keys, or credentials
- **Service accounts**: Cloud Run default compute SA needs `roles/secretmanager.secretAccessor`
- **CORS**: Currently allows all origins (restrict in production if needed)

## Known Limitations & Gotchas

1. **Cold start**: First API request after idle takes ~10s (Cloud Run scales to zero)
2. **Video timeout**: Default 300s, can be increased but costs more
3. **Image size**: ModelArk requires min 300px height (267px will fail with cryptic error)
4. **Metrics persistence**: In-memory only, resets on container restart
5. **No video download**: Videos returned as URLs (hosted by ModelArk), not stored locally
6. **Dashboard API URL**: Must be set via `API_URL` env var (defaults to localhost)

## BytePlus ModelArk Specifics

### API Authentication
```python
headers = {
    "Authorization": f"Bearer {ARK_API_KEY}",
    "Content-Type": "application/json"
}
```

### Endpoint Structure
- Base: `https://ark.ap-southeast.bytepluses.com/api/v3`
- Script: `POST /chat/completions` (OpenAI-compatible)
- Video task: `POST /contents/generations/tasks`
- Video status: `GET /contents/generations/tasks/{task_id}`

### Response Formats
- **Script**: Standard OpenAI format with `usage.prompt_tokens`, `usage.completion_tokens`
- **Video task**: Returns `{"id": "task_id", ...}`
- **Video status**: Returns `{"status": "succeeded|failed|processing", "content": {"video_url": "..."}}`

### Rate Limits
- Not explicitly documented, but honors `Retry-After` header
- Recommended: 2-10 concurrent video generations
- Script generation: Higher throughput than video

## Repository Organization Note

This repo follows **Google/Kubernetes/Terraform standards**:
- Platform-separated deployment configs in `deploy/`
- Layered documentation in `docs/` (architecture, guides, API)
- Working examples in `examples/`
- Test structure in `tests/` (unit, integration, fixtures)
- Single-entry Makefile for all common tasks
- Community files: CONTRIBUTING.md, SECURITY.md, CHANGELOG.md
