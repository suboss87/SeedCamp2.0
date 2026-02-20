# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AdCamp** — Enterprise AI video generation pipeline for D2C e-commerce. Generates platform-optimized product videos using BytePlus ModelArk's Seed and Seedance models. The core differentiator is **smart model routing**: Hero SKUs (top 20%) route to premium Seedance Pro, Catalog SKUs (80%) route to cost-optimized Pro Fast, achieving $0.08/video average.

## Common Commands

```bash
# Setup
make install                              # Create venv, install deps

# Development
make dev                                  # API on :8000 + Streamlit on :8501
source venv/bin/activate && uvicorn app.main:app --reload --port 8000  # API only

# Testing
make test                                 # pytest with coverage
pytest tests/unit/test_model_router.py -v # Single test file
pytest -k "test_hero" -v                  # Pattern match

# Linting
make lint                                 # ruff + black (check only)
black app/ dashboard/                     # Auto-format
ruff check app/ --fix                     # Auto-fix lint

# Docker
make docker-build                         # Build: root Dockerfile
make docker-up                            # docker-compose up
make docker-down                          # docker-compose down

# Deploy GCP Cloud Run
export GCP_PROJECT_ID=your-gcp-project-id && make deploy-gcp
```

## Architecture

### 5-Step Pipeline (app/main.py orchestrates)

1. **Input** — `GenerateRequest` (brief, image URL, SKU tier, platforms, duration)
2. **Script Gen** — `app/services/script_writer.py` calls Seed 1.8 via OpenAI-compatible API, returns `(AdScript, input_tokens, output_tokens)`
3. **Smart Router** — `app/services/model_router.py` dict-based routing: `route(sku_tier) -> (model_id, cost_per_m)`
4. **Video Gen** — `app/services/video_gen.py` async task creation + polling via ModelArk REST API
5. **Output** — Platform-ready MP4 URLs

### Key Patterns

- **All services are async** — use `httpx.AsyncClient` (not `requests`), `asyncio.sleep()` for polling
- **`@retry_with_backoff` decorator** (`app/utils/retry.py`) wraps all ModelArk API calls with exponential backoff, rate-limit honoring (Retry-After header), and error classification
- **Script writer uses OpenAI SDK** (`AsyncOpenAI`) because ModelArk is OpenAI-compatible; video gen uses raw `httpx` because the video task API is ModelArk-specific
- **Cost tracking flows through every step** — tokens counted at script gen, estimated at video gen, aggregated in `app/services/cost_tracker.py`
- **Config via Pydantic Settings** (`app/config.py`) — reads from `.env`, typed model IDs and cost constants
- **Monitoring is in-memory** (`app/monitoring.py`) — Prometheus-compatible text format at `/metrics`, resets on restart

### Data Flow

`GenerateRequest` → `script_writer.generate_script()` → `model_router.route()` → `video_gen.create_video_task()` → returns `GenerateResponse` with `task_id` → client polls `/api/status/{task_id}` or blocks on `/api/wait/{task_id}`

### API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/generate` | POST | Full pipeline (steps 1-4), returns task_id |
| `/api/generate-stream` | POST | Full pipeline with SSE progress streaming |
| `/api/upload-image` | POST | Upload product image to GCS, returns public URL |
| `/api/status/{task_id}` | GET | Poll video generation status |
| `/api/wait/{task_id}` | GET | Block until video ready |
| `/api/cost-summary` | GET | Aggregate cost tracking |
| `/health` | GET | Health + model config |
| `/metrics` | GET | Prometheus text format |
| `/health/detailed` | GET | Extended health status |

### Deployment Layout

`deploy/` is organized by platform: `docker/` (docker-compose references root `Dockerfile`), `gcp/` (Cloud Run + Terraform), `aws/` (ECS Fargate + Terraform), `byteplus/` (VKE K8s manifests), `monitoring/` (Prometheus + Grafana).

## Critical Constraints

- **ModelArk images must be >=300px height** — validate before sending or you get cryptic 400 errors
- **Non-retryable errors**: `InvalidAPIKeyError`, `QuotaExceededError` — retry logic skips these intentionally
- **Video polling timeout**: 300s default (`settings.poll_timeout`), 5s interval
- **CORS is wide open** (`allow_origins=["*"]`) — intentional for current stage
- **Metrics not persisted** — in-memory only, resets on container restart
- **Dashboard needs `API_URL` env var** — defaults to localhost, must be set for deployed environments

## Commit Convention

```
feat: add batch video generation endpoint
fix: resolve rate limit handling in retry logic
docs: update GCP deployment guide
test: add model router unit tests
refactor: extract cost calculation logic
chore: update dependencies
```

## Environment Variables

Required: `ARK_API_KEY`

Optional (with defaults in `app/config.py`): `ARK_BASE_URL`, `script_model`, `video_model_pro`, `video_model_fast`, cost constants, `video_duration`, `video_resolution`, `poll_interval`, `poll_timeout`

---

## Workflow Orchestration

### 1. Plan First

- Enter plan mode for any non-trivial task with three or more steps or architectural decisions
- If something goes sideways, stop and re-plan immediately — do not keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specifications upfront to reduce ambiguity

### 2. Subagent Strategy

- Use subagents liberally to keep the main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, allocate more compute through subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop

- After any correction from the user, update `tasks/lessons.md` with the pattern
- Write rules that prevent the same mistake from recurring
- Ruthlessly iterate on these lessons until the mistake rate drops
- Review lessons at session start for the relevant project

### 4. Verification Before Done

- Never mark a task complete without proving it works
- Compare behavior between main and your changes when relevant
- Ask yourself: would a staff engineer approve this?
- Run tests, check logs, and demonstrate correctness

### 5. Demand Elegance (Balanced)

- For non-trivial changes, pause and ask if there is a more elegant way
- If a fix feels hacky, implement the elegant solution based on everything you now know
- Skip this for simple and obvious fixes — do not over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing

- When given a bug report, fix it without asking for hand-holding
- Identify logs, errors, and failing tests, then resolve them
- Require zero context switching from the user
- Fix failing CI tests without being told how

## Task Management

All task tracking lives in `tasks/`:

1. **Plan First** — write the plan to `tasks/todo.md` with checkable items
2. **Verify Plan** — check in before starting implementation
3. **Track Progress** — mark items complete as you go
4. **Explain Changes** — provide a high-level summary at each step
5. **Document Results** — add a review section to `tasks/todo.md`
6. **Capture Lessons** — update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First** — make every change as simple as possible, impact minimal code
- **No Laziness** — find root causes, avoid temporary fixes, maintain senior developer standards
- **Minimal Impact** — changes should only touch what is necessary, avoid introducing bugs
