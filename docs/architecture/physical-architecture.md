# SeedCamp Video Generation Pipeline -- Physical Architecture

## Overview

The physical architecture describes **what runs where** -- processes, ports, protocols, APIs, and infrastructure components.

## Deployment Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LOCAL MACHINE (macOS / Linux / Windows)                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                                                             │    │
│  │  ┌─────────────────────┐     HTTP      ┌────────────────┐  │    │
│  │  │  STREAMLIT DASHBOARD│    :8501      │  FASTAPI       │  │    │
│  │  │  dashboard/app.py   │◄────────────▶│  app/main.py   │  │    │
│  │  │  Port 8501          │  localhost    │  Port 8000     │  │    │
│  │  │                     │              │                │  │    │
│  │  │  • Campaign form    │              │  • /api/generate│  │    │
│  │  │  • SKU tier select  │              │  • /api/status  │  │    │
│  │  │  • Video player     │              │  • /api/wait    │  │    │
│  │  │  • Cost metrics     │              │  • /api/cost-   │  │    │
│  │  │                     │              │    summary      │  │    │
│  │  └─────────────────────┘              └───────┬────────┘  │    │
│  │                                               │            │    │
│  │  ┌─────────────────────┐                      │            │    │
│  │  │  LOCAL FILE SYSTEM  │◄─────────────────────┤            │    │
│  │  │  output/            │   Write MP4s         │            │    │
│  │  │  • SKU_tiktok.mp4   │                      │            │    │
│  │  │  • SKU_instagram.mp4│                      │            │    │
│  │  │  • SKU_youtube.mp4  │                      │            │    │
│  │  └─────────────────────┘                      │            │    │
│  │                                                │            │    │
│  │  ┌─────────────────────┐                      │            │    │
│  │  │  .env               │                                   │    │
│  │  │  ARK_API_KEY=***    │                                   │    │
│  │  └─────────────────────┘                                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                    │                                │
│                                    │ HTTPS (Bearer Token)           │
│                                    ▼                                │
│  BYTEPLUS CLOUD (ap-southeast)                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ark.ap-southeast.bytepluses.com/api/v3                     │    │
│  │                                                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │  SEED 1.8    │  │ SEEDANCE     │  │ SEEDANCE         │  │    │
│  │  │              │  │ 2.0          │  │ 2.0 FAST         │  │    │
│  │  │ /chat/       │  │              │  │                  │  │    │
│  │  │ completions  │  │ /video/      │  │ /video/          │  │    │
│  │  │              │  │ generations  │  │ generations      │  │    │
│  │  │ Sync REST    │  │ Async REST   │  │ Async REST       │  │    │
│  │  │ ~2-5 sec     │  │ ~30-120 sec  │  │ ~10-40 sec       │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │    │
│  │                                                             │    │
│  │  API Pattern:                                               │    │
│  │  • Seed 1.8 ──▶ Synchronous (request/response)             │    │
│  │  • Seedance  ──▶ Asynchronous (create task ──▶ poll status) │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend -- Streamlit Dashboard
| Property | Value |
|----------|-------|
| File | `dashboard/app.py` |
| Port | 8501 |
| Protocol | HTTP (localhost) |
| Role | User interface for campaign input, video preview, cost tracking |
| Dependencies | `requests` (HTTP client to FastAPI backend) |

### Backend -- FastAPI Application
| Property | Value |
|----------|-------|
| File | `app/main.py` |
| Port | 8000 |
| Protocol | HTTP REST API |
| Role | Pipeline orchestration, model routing, cost calculation |
| Dependencies | `openai` (Seed 1.8), `httpx` (Seedance API), `asyncio` (polling) |

### External API -- BytePlus ModelArk
| Property | Value |
|----------|-------|
| Base URL | `https://ark.ap-southeast.bytepluses.com/api/v3` |
| Auth | Bearer token (`ARK_API_KEY`) |
| Region | ap-southeast |
| Protocol | HTTPS REST |

### Storage -- Local File System
| Property | Value |
|----------|-------|
| Directory | `output/` |
| Format | MP4 (H.264 video, AAC audio) |
| Naming | `{SKU_ID}_{platform}_{width}x{height}.mp4` |

## API Contracts

### Seed 1.8 -- Synchronous
```
POST /chat/completions
├── Request:  { model, messages, temperature, max_tokens }
├── Response: { choices[0].message.content (JSON string) }
└── Latency:  ~2-5 seconds
```

### Seedance -- Asynchronous (2-step)
```
Step 1: POST /video/generations
├── Request:  { model, content: [{type, text/image_url}] }
├── Response: { id: "task_id" }
└── Latency:  ~1 second

Step 2: GET /video/generations/{task_id}
├── Response: { status, content[].video_url }
├── Poll every 5 seconds
├── Pro Fast latency: ~10-40 seconds (catalog 80%)
└── Pro latency:      ~30-120 seconds (hero 20%)
```

## Network Flow

```
Browser ──HTTP──▶ Streamlit (:8501) ──HTTP──▶ FastAPI (:8000)
                                                 │
                                    ┌────────────┼────────────┐
                                    │            │            │
                                 HTTPS        HTTPS
                                    │            │
                                    ▼            ▼
                               Seed 1.8    Seedance
                               (sync)     (async)
```

## Production Scaling Notes

For production deployment (beyond POC), the architecture would extend to:

- **Backend:** Deploy FastAPI on AWS ECS / GCP Cloud Run behind an ALB
- **Storage:** Replace local filesystem with S3 / GCS for generated assets
- **CDN:** CloudFront / Fastly for video delivery to platforms
- **Queue:** Replace polling with SQS / Pub-Sub for async video tasks
- **Database:** PostgreSQL for cost tracking, job history, SKU metadata
- **Auth:** API key management via AWS Secrets Manager / Vault
