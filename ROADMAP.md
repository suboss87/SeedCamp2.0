# SeedCamp Roadmap

SeedCamp is an open-source **reference architecture** for AI video generation
pipelines. The roadmap reflects that: we invest in patterns that are reusable and
honest about their limits, not in chasing feature breadth.

Scope is deliberately narrow. If something isn't here, it's probably an
intentional non-goal (see bottom).

## v1.0 — Credible, honest launch (current)

- [x] 5 reusable pipeline patterns (routing, async, cost, batch, retry)
- [x] Safety + quality evaluation gates
- [x] FastAPI service + Streamlit dashboard
- [x] Dry-run mode (full pipeline, zero API cost)
- [ ] **Cost numbers reconciled against a real ModelArk invoice**
      (`scripts/reconcile_cost.py`) — *blocks publishing any per-video figure*
- [ ] **Real-API smoke test green** (`scripts/smoke_test.py`) — *blocks claiming
      the happy path works*
- [ ] Sora → Seedance migration as the front-door story

## v1.1 — Scale-out (the durability layer)

These turn "low hundreds, best-effort" into "inventory-scale, resumable". See
[docs/SCALING.md](docs/SCALING.md) for the design.

- [ ] Durable job queue + idempotent, resumable batch jobs
- [ ] API / worker process split
- [ ] Shared cost/metrics/rate-limit state (Redis)
- [ ] Postgres persistence backend + migrations

## v1.2 — Provider choice

- [ ] Provider abstraction so the video step isn't BytePlus-only
- [ ] Adapters: Veo, Kling, Runway (community-contributable)
- [ ] Per-provider cost models feeding the same routing/budget logic

## Good first issues (help wanted)

Concrete, scoped, and genuinely useful — good entry points for contributors:

1. Postgres persistence backend implementing the `persistence` interface.
2. Redis-backed cost tracker so `/api/cost-summary` is correct under >1 worker.
3. Idempotency key on `_process_product` (safe re-delivery).
4. Provider adapter scaffold + a single non-BytePlus adapter behind a flag.
5. A `make smoke` target wrapping `scripts/smoke_test.py`.
6. Dashboard: surface per-campaign cost vs. budget as a live bar.
7. Golden-file tests for the safety/quality JSON parsers (malformed-LLM-output cases).
8. Docs: a 5-minute "fork it for your vertical" tutorial.

## Non-goals (on purpose)

- Becoming a hosted SaaS or visual editor.
- A template/layout-swap video tool (different problem).
- Feature parity with managed platforms (Synthesia/HeyGen/Runway).
