# D2C Video Ad Pipeline 🎬

AI-Powered Product Video Generation at Scale with **BytePlus ModelArk**.

Working POC for the D2C Video Ad Pipeline Solution Brief — proves the architecture, smart model routing, and $0.27/video cost target.

## Solution Architecture

```
1. INPUT        → Product image, brand assets, campaign brief
2. SEED 1.8     → Script generation: ad copy, scene descriptions
3. MODEL ROUTER → Hero SKUs → Seedance Pro | Catalog SKUs → Pro Fast
4. SEEDANCE     → Video generation: product showcases, lifestyle scenes
5. FFMPEG       → Post-processing: platform-specific format/resolution
6. OUTPUT       → Platform-ready assets (TikTok, Instagram, YouTube)
```

## Smart Model Routing

| SKU Tier | Model | Use Case | Pricing |
|----------|-------|----------|---------|
| Hero SKUs (Top 20%) | Seedance 1.5 Pro | Highest quality, cinematic | $1.20/M tokens |
| Catalog SKUs (80%) | Seedance 1.0 Pro Fast | Fast, cost-optimized | $0.70/M tokens |
| Ad Scripts & Copy | Seed 1.8 | Script generation | $0.25 in / $2.00 out |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your BytePlus ModelArk API key to .env
```

## Run

```bash
# Backend
uvicorn app.main:app --reload --port 8000

# Dashboard (separate terminal)
streamlit run dashboard/app.py --server.port 8501
```

## API Endpoints

- `POST /api/generate` — Full pipeline: brief → script → route → video
- `GET /api/status/{task_id}` — Poll video generation status
- `GET /api/wait/{task_id}` — Block until video ready (demo)
- `GET /api/cost-summary` — Aggregate cost tracking
- `GET /health` — Health check with model config

## POC Success Criteria

- ✅ 80%+ first-pass brand approval rate
- ⚡ < 60 seconds per video generation
- 💰 < $0.50 per video (blended average)

## Cost Target

2,500 SKUs × 3 variants × 30% monthly refresh = 34,500 annual videos

**$0.16/video on ModelArk** | Annual TCO: $7,600

Annual savings: $35K vs Sora | $10K vs Runway | $16K vs Kling
