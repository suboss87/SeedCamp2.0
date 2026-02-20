# Examples

Runnable scripts demonstrating AdCamp API usage.

## Prerequisites

```bash
# Install dependencies (includes httpx)
make install
source venv/bin/activate

# Start the API
make dev
```

## Scripts

### `generate_single_video.py`

Generate one product video end-to-end: submit a brief, poll for completion, get the video URL.

```bash
python3 examples/generate_single_video.py
```

### `batch_campaign.py`

Full campaign workflow: create a campaign, upload a product CSV, trigger batch generation, and monitor progress.

**Requires Firestore** — set `GOOGLE_APPLICATION_CREDENTIALS` or run in a GCP environment.

```bash
python3 examples/batch_campaign.py
```

## Environment

Both scripts default to `http://localhost:8000`. Set `ARK_API_KEY` in your `.env` file before running.
