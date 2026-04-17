# Examples

Runnable scripts demonstrating SeedCamp API usage across industries.

## Prerequisites

```bash
# Install dependencies (includes httpx)
make install
source venv/bin/activate

# Start the API (DRY_RUN=true works without API keys)
DRY_RUN=true make dev
```

## Core Scripts

### `generate_single_video.py`

Generate one product video end-to-end: submit a brief, poll for completion, get the video URL.

```bash
python3 docs/examples/generate_single_video.py
```

### `batch_campaign.py`

Full campaign workflow: create a campaign, upload a product CSV, trigger batch generation, and monitor progress.

**Requires Firestore** -- set `GOOGLE_APPLICATION_CREDENTIALS` or run in a GCP environment.

```bash
python3 docs/examples/batch_campaign.py
```

## Industry Examples

These scripts demonstrate how SeedCamp's tiered routing adapts to different verticals. Each one submits a batch of items with realistic briefs and prints a cost summary showing the hero/standard split.

### `automotive_dealer.py`

Dealership scenario with 300+ vehicles. Featured/certified vehicles route to the premium model; bulk used inventory routes to the fast model.

```bash
python3 docs/examples/automotive_dealer.py
```

### `ecommerce_catalog.py`

E-commerce scenario with 1K-100K SKUs. Top-revenue hero products get premium video; long-tail catalog items get cost-optimized video.

```bash
python3 docs/examples/ecommerce_catalog.py
```

### `real_estate_listing.py`

Real estate scenario with 500+ listings. Luxury properties ($1M+) get cinematic walkthroughs; standard listings get quick virtual tours.

```bash
python3 docs/examples/real_estate_listing.py
```

## Environment

All scripts default to `http://localhost:8000`. Set `DRY_RUN=true` to run without a BytePlus API key, or set `ARK_API_KEY` in your `.env` file for real generation.
