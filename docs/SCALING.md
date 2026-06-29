# Scaling SeedCamp

**Read this before you point SeedCamp at thousands of SKUs.** The default
configuration is deliberately simple so the patterns are easy to read and fork.
That simplicity has a ceiling. This document is honest about where that ceiling
is and exactly what to change to go past it.

## What the default architecture actually is

Out of the box, SeedCamp runs as a **single process**:

- Batch generation is a **fire-and-forget `asyncio.create_task`** inside the
  FastAPI process (`app/routes/campaigns.py`, `app/services/batch_generator.py`).
- Cost tracking and metrics are **in-memory** (`app/services/cost_tracker.py`,
  `app/monitoring.py`).
- Persistence defaults to an **in-memory store** (`PERSISTENCE_BACKEND=memory`).
- Rate limiting state (`slowapi`) is **in-process**.

This is the right design for what most people need on day one: a single operator
generating **up to a few hundred videos** per run, on one box, with the dashboard
open. It is tested (139 tests) and predictable.

## The ceiling (know these before you scale)

| Limit | Why | Symptom |
|---|---|---|
| **No durable job queue** | The batch lives in the request process's event loop. | A restart / redeploy / OOM / pod reschedule **loses all in-flight work** with no resume. |
| **Single-process state** | Cost, metrics, and rate limits are per-process. | Run >1 worker and `/api/cost-summary` returns partial data (a startup warning already flags this). |
| **API and generation share a process** | No worker separation. | A large batch starves HTTP responsiveness; you can't scale generation independently. |
| **Provider throughput** | Seedance beta ≈ 2 RPS / 3 concurrent per account; default `batch_concurrency=3`. | 10K videos at 3-wide is **days** of wall-clock — exactly when crashes happen, and the default design can't resume. |

**Bottom line:** the default is "one operator, low hundreds of videos, best-effort."
For inventory-scale workloads (10K–100K SKUs) you must add the layers below.

## The scale-out path

```mermaid
graph LR
    subgraph API tier (stateless, autoscale)
        A[FastAPI: accept campaign, enqueue jobs]
    end
    subgraph Queue (durable)
        Q[(Cloud Tasks / SQS / Celery+Redis)]
    end
    subgraph Worker tier (autoscale, idempotent)
        W1[Worker: brief→script→safety→video→quality]
        W2[Worker: ...]
    end
    subgraph Shared state
        DB[(Postgres: campaigns, products, results)]
        R[(Redis: cost counters, rate limits, metrics)]
    end
    A --> Q --> W1 & W2
    W1 & W2 --> DB
    W1 & W2 --> R
    A --> DB
```

Implement in this order:

1. **Durable queue + idempotent jobs.** Replace the `asyncio.create_task` batch
   dispatch with enqueue-to-queue. Make `_process_product` idempotent on
   `{campaign_id}_{product_id}` so a re-delivered job is safe. This single change
   removes the "lose everything on restart" failure and gives you resume.
2. **Worker / API split.** Run generation in dedicated workers that pull from the
   queue; keep the FastAPI tier stateless so it can autoscale behind a load
   balancer.
3. **Shared cost/metrics/rate-limit state.** Move `cost_tracker` counters and
   `slowapi` limits to Redis (or Postgres) so aggregates are correct across
   workers. The `persistence` abstraction already isolates the storage swap.
4. **Durable persistence.** Use Postgres (or the wired-in Firestore) instead of
   the memory store. Add a migration for `campaigns` / `products` / `video_results`.
5. **Backpressure to the provider.** Centralize the concurrency budget (a Redis
   token bucket) so all workers collectively respect ModelArk's RPS/concurrency
   limits instead of each worker guessing.

## How to be honest about it publicly

If you have not implemented the above, **do not claim 10K–100K scale.** Claim what
is true: *"a clean, tested reference architecture and a working pipeline for up to
a few hundred videos per run; here is the documented path to scale it out."* That
honesty is what earns trust in an open-source project — see the roadmap in
[../ROADMAP.md](../ROADMAP.md), where durable batch execution is the top item.
