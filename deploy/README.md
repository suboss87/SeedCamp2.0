# Deployment Guide

SeedCamp runs as a standard Python ASGI app. Pick the deployment target that matches your infrastructure and scale.

> **Not here:** Configuration (see `.env.example`), troubleshooting (see `docs/TROUBLESHOOTING.md`).

---

## Which Target Should I Use?

| | Docker (local) | Cloud Run | AWS ECS | BytePlus VKE | Railway / Render |
|---|---|---|---|---|---|
| **Best for** | Dev, testing, on-prem | Most production use cases | AWS-native teams | BytePlus-native infra | Fast deploys, no DevOps |
| **Scale to zero** | No | Yes | With Fargate | No | Yes (Render) |
| **Cold start** | None | 1-3s | 2-5s | None | 1-5s |
| **Concurrent requests** | Limited by local RAM | Configurable, managed | Configurable | Configurable | Limited (free tier) |
| **Cost model** | Fixed (your hardware) | Per request + idle | Per task hour | Node pool (always-on) | Per GB-hour or flat |
| **Setup complexity** | Lowest | Low | Medium | Medium | Lowest |
| **Cost tracker accuracy** | Full (WORKERS=1) | Full (WORKERS=1) | Full (WORKERS=1) | Multi-worker — see note | Full (WORKERS=1) |
| **Persistent output storage** | Local disk | GCS (recommended) | S3 | Object Storage | Ephemeral — use GCS/S3 |

**Rule of thumb:**
- Starting out or testing: **Docker**
- Shipping to production on GCP: **Cloud Run**
- Shipping to production on AWS: **ECS with Fargate**
- Already running BytePlus infrastructure: **VKE**
- Just want it running fast without ops: **Railway or Render**

---

## Cost Tracker Note for Multi-Worker Deployments

The built-in cost tracker is in-memory and **per-worker**. If you run `WORKERS > 1`, each worker tracks its own costs independently — totals on `/metrics` will be incomplete.

Options:
- Set `WORKERS=1` for accurate in-process cost totals (works for most production loads)
- Use an external aggregator (Prometheus + Grafana) with the `/metrics` endpoint — this works regardless of worker count
- Set `PERSISTENCE_BACKEND=postgres` to route cost records to a shared database (requires schema setup)

---

## Docker (Local / On-Prem)

```bash
# Build
docker build -t seedcamp .

# Run
docker run -p 8000:8000 \
  -e ARK_API_KEY=your_key \
  -e DRY_RUN=false \
  -v $(pwd)/output:/app/output \
  seedcamp
```

The API is available at `http://localhost:8000`. Dashboard at `http://localhost:8501` (run separately via `streamlit run dashboard/app.py`).

**Worker count:** Default is 1. Increase with `-e WORKERS=4` only if you need higher throughput — see cost tracker note above.

---

## Cloud Run (GCP)

Cloud Run is the recommended production target for most teams. It scales to zero, handles spikes, and integrates with GCS for video output storage.

```bash
# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT/seedcamp

# Deploy
gcloud run deploy seedcamp \
  --image gcr.io/YOUR_PROJECT/seedcamp \
  --platform managed \
  --region us-central1 \
  --set-env-vars ARK_API_KEY=your_key \
  --memory 2Gi \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 5 \
  --allow-unauthenticated
```

**Storage:** Set `GCS_BUCKET=your-bucket` and ensure the Cloud Run service account has `roles/storage.objectCreator`.

**Secrets:** Use Secret Manager instead of env vars for `ARK_API_KEY` in production:
```bash
gcloud secrets create ark-api-key --data-file=- <<< "your_key"
gcloud run services update seedcamp --update-secrets ARK_API_KEY=ark-api-key:latest
```

---

## AWS ECS with Fargate

For AWS-native teams. Push to ECR, deploy via ECS.

```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com
docker tag seedcamp ACCOUNT.dkr.ecr.REGION.amazonaws.com/seedcamp:latest
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/seedcamp:latest
```

**Task definition:** Set CPU to 512, memory to 1024 (minimum). Store `ARK_API_KEY` in AWS Secrets Manager and reference it in the task definition — do not pass it as a plain env var.

**Output storage:** Mount an EFS volume or write directly to S3 via `boto3` (requires a small addition to `video_gen.py`).

---

## BytePlus VKE (Kubernetes)

For teams already running BytePlus infrastructure. VKE is managed Kubernetes on BytePlus Cloud.

See `deploy/byteplus/vke/` for Kubernetes manifests. Key settings:

```yaml
# Recommended resource requests
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

Store `ARK_API_KEY` in a Kubernetes Secret, not in the manifest.

**Advantage:** Lowest latency to BytePlus ModelArk API endpoints — useful for high-throughput batch jobs.

---

## Railway

One-command deploy. Suited for prototypes and small production workloads.

1. Connect your GitHub fork to Railway
2. Add env vars in Railway dashboard: `ARK_API_KEY`, `DRY_RUN=false`
3. Railway auto-deploys on push to main

**Limitation:** Ephemeral filesystem — generated videos are lost on restart. Set `GCS_BUCKET` and write outputs to GCS, or mount a Railway volume.

---

## Render

Similar to Railway. Use the `render.yaml` in `deploy/render/` if present, or configure manually:

- **Environment:** Python
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Disk:** Mount a persistent disk at `/app/output` to retain generated videos

---

## Health and Metrics

All deployments expose:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check — returns `{"status": "ok"}` |
| `GET /metrics` | Cost totals, request counts, pipeline stats |

Configure your load balancer or uptime monitor to hit `/health` every 30s.
