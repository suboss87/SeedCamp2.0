# SeedCamp Video Generation Pipeline — Logical Architecture

## Overview

The logical architecture describes the **business logic flow** — what happens at each step, how data transforms, and the routing decisions that drive cost optimization.

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VIDEO GENERATION PIPELINE                         │
│                       (Logical Architecture)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    Campaign Brief                                     │
│  │  BRAND   │    + Product Image     ┌──────────────────────┐       │
│  │  TEAM    │───────────────────────▶│   1. INPUT LAYER     │       │
│  │ (User)   │    + SKU Tier          │   Validate & enrich  │       │
│  └──────────┘    + Target Platforms   └──────────┬───────────┘       │
│                                                  │                  │
│                                                  ▼                  │
│                                      ┌──────────────────────┐       │
│                                      │  2. SCRIPT WRITER    │       │
│                                      │     (Seed 1.8)       │       │
│                                      │                      │       │
│                                      │  Brief ──▶ Ad Copy   │       │
│                                      │       ──▶ Scene Desc │       │
│                                      │       ──▶ Video Prompt│      │
│                                      │       ──▶ Camera Dir │       │
│                                      └──────────┬───────────┘       │
│                                                  │                  │
│                                                  ▼                  │
│                                      ┌──────────────────────┐       │
│                                      │  3. MODEL ROUTER     │       │
│                                      │  (Business Logic)    │       │
│                                      │                      │       │
│                                      │  Hero (20%) ─▶ Pro   │       │
│                                      │  Catalog (80%) ─▶Fast│       │
│                                      └──────────┬───────────┘       │
│                                                  │                  │
│                              ┌────────────────┬──┘                  │
│                              ▼                ▼                     │
│                 ┌──────────────────┐ ┌──────────────────┐           │
│                 │ 4a. SEEDANCE     │ │ 4b. SEEDANCE     │           │
│                 │  1.5 PRO         │ │  1.0 PRO FAST    │           │
│                 │  (Cinematic)     │ │  (Cost-optimized) │          │
│                 │  $1.20/M tokens  │ │  $0.70/M tokens  │           │
│                 └────────┬─────────┘ └────────┬─────────┘           │
│                          └────────┬───────────┘                     │
│                                   ▼                                 │
│                       ┌──────────────────────┐                      │
│                       │  5. OUTPUT & COST    │                      │
│                       │  Platform-ready MP4  │                      │
│                       │  + Cost per video    │                      │
│                       │  ~$0.09/video blend  │                      │
│                       └──────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Transformations

| Step | Input | Output | Model / Tool |
|------|-------|--------|-------------|
| 1. Input | Campaign brief, product image, SKU tier, platforms | Validated request | — |
| 2. Script Writer | Campaign brief (text) | Ad copy, scene description, video prompt, camera direction | Seed 1.8 |
| 3. Model Router | SKU tier (hero / catalog) | Model ID + cost rate | Business logic |
| 4. Video Gen | Video prompt + optional image | Raw MP4 video (720p/1080p, 2-12s) | Seedance Pro or Pro Fast |
| 5. Output | Video URL + cost data | Platform-ready MP4 + cost breakdown | Cost Tracker |

## Smart Model Routing Logic

```
if sku_tier == "hero":       # Top 20% high-value products
    model = Seedance 1.5 Pro         # $1.20/M tokens — cinematic quality
else:                         # Catalog 80%
    model = Seedance 1.0 Pro Fast    # $0.70/M tokens — 3x faster, 72% cheaper
```

**Business rationale:** Hero SKUs (flagship products, campaign heroes) justify higher spend for premium video quality. Catalog SKUs (long-tail products) need volume at low cost — Pro Fast delivers acceptable quality at 3x the speed and 72% lower cost.

## Platform Output Specs

| Platform | Aspect Ratio | Resolution | Use Case |
|----------|-------------|------------|----------|
| TikTok | 9:16 | 720×1280 | Short-form vertical video ads |
| Instagram | 1:1 | 720×720 | Feed posts, Reels square format |
| YouTube | 16:9 | 1280×720 | Pre-roll ads, Shorts horizontal |
