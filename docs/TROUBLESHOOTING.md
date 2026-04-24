# Troubleshooting

> **Scope:** Diagnosing failures during pipeline execution — evaluator scores, API errors, retries, and cost warnings.
> **Not here:** Deployment failures (see `deploy/README.md`), configuration (see `.env.example`), migration from Sora (see `docs/MIGRATE_FROM_SORA.md`).

---

## Safety Evaluator Failures

The safety evaluator runs before video generation. A blocked script never reaches the model.

| Symptom | Likely cause | What to do |
|---------|-------------|------------|
| `recommendation: "block"` — script rejected | Overall safety score >= 0.8 | Read `flagged_issues` in the response — it names the specific concern. Rewrite the script prompt to remove the flagged element |
| Score high on `brand_safety` | Script implies competitor comparison, legal claims, or controversy | Remove superlatives ("best", "only"), legal language, or references to competitors |
| Score high on `bias` or `stereotypes` | Prompt is too demographic-specific | Broaden the audience framing in your product brief |
| Score high on `cultural_insensitivity` | Product copy uses culture-specific idioms | Rewrite brief in neutral English; let the script writer generalize |
| Score high on `violence` or `sexual_content` | Product brief contains ambiguous language | Review your brief for terms that read differently out of context |
| Safety evaluator returns `null` / crashes silently | Seed 1.8 API error during classification | Check `ARK_API_KEY` is valid; check logs for `429` or `401`; enable `dry_run=true` to bypass for testing |
| You want to skip safety for internal testing | `SAFETY_ENABLED=false` in `.env` | **Only do this locally.** Never disable safety in production — BytePlus will reject unsafe prompts at generation time anyway; you just move the failure downstream |

**Threshold reference** (configurable in `.env`):

| Variable | Default | Meaning |
|---|---|---|
| `SAFETY_THRESHOLD_FLAG` | 0.3 | Score above this is `low_risk` |
| `SAFETY_THRESHOLD_HIGH_RISK` | 0.6 | Score above this is `high_risk` |
| `SAFETY_THRESHOLD_BLOCK` | 0.8 | Score above this blocks the script |

---

## Quality Evaluator Failures

Quality evaluation is **non-blocking** — a failed quality eval logs a warning and returns `quality: null`, but the video still generates.

| Symptom | Likely cause | What to do |
|---------|-------------|------------|
| `prompt_clarity` score low | Video prompt is vague or ambiguous | Add specific visual instructions: camera movement, lighting, subject position |
| `brand_alignment` score low | Script doesn't reference product name, category, or unique value | Feed a richer product brief with brand voice guidelines |
| `creative_quality` score low | Script is generic — could describe any product | Add product-specific hooks: texture, use case, emotion |
| `technical_precision` score low | Duration, resolution, or ratio mismatch in prompt | Verify `video_duration`, `video_resolution`, and platform ratio are set correctly |
| `platform_fit` score low | Script style doesn't match target platform | TikTok needs energy and hooks in the first 2s; YouTube tolerates longer narratives; Instagram favors aesthetics |
| Quality eval always returns `null` | Seed 1.8 API error | Check logs; quality eval failures are intentionally silent — look for `WARNING quality evaluation failed` |
| You want to enforce quality as a gate | Wrap `evaluate_video_quality()` result and raise if score < threshold | Not default — quality is advisory, not blocking. Add this in `app/main.py` if your use case requires it |

---

## Video Generation Failures

| Symptom | Likely cause | What to do |
|---------|-------------|------------|
| `401 Unauthorized` | `ARK_API_KEY` missing or wrong | Check `.env`; run `python -c "from app.config import settings; print(settings.ark_api_key[:8])"` to verify key is loaded |
| `429 Rate Limit` | Too many concurrent requests | Reduce `BATCH_CONCURRENCY_DEFAULT` (default: 3); the retry logic honors `Retry-After` headers automatically |
| `403 Quota Exceeded` | Account quota exhausted | Log into BytePlus console and check your ModelArk quota; this is a quota error, not a key error — retrying won't help |
| Task stuck in `Running` for > 5 minutes | BytePlus server-side processing delay | Poll timeout is 300s by default (`POLL_TIMEOUT`). Increase if needed. Check BytePlus status page |
| Task returns `Failed` with no message | Prompt flagged server-side by BytePlus | Your prompt passed local safety evaluation but failed BytePlus platform safety. Rewrite the prompt more conservatively |
| `httpx.TimeoutException` on task creation | Network or BytePlus API latency spike | Retry logic handles this automatically (3 retries, 2s initial delay). If persistent, check BytePlus regional endpoint |
| All retries exhausted | Sustained API outage or credential issue | Check logs for last exception type; `InvalidAPIKeyError` and `QuotaExceededError` are not retried — fix the root cause |

---

## Model Routing

| Symptom | Likely cause | What to do |
|---------|-------------|------------|
| All SKUs routing to Pro | `sku_tier` always set to `hero` | Check your `GenerateRequest` — `sku_tier` defaults to `hero` if not set. Pass `sku_tier="catalog"` for standard SKUs |
| You want all SKUs on Pro for a launch | Override via `sku_tier="hero"` on every request | This works but costs 30% more than catalog routing — verify it's intentional |
| Custom tier logic needed | Two tiers (hero/catalog) not enough | Extend `SKUTier` enum in `app/models/schemas.py` and add a route in `app/services/model_router.py` |

**Model ID reference:**

| Tier | Model ID | Cost |
|------|----------|------|
| Hero (Pro) | `dreamina-seedance-2-0-260128` | $4.30/M tokens |
| Catalog (Fast) | `dreamina-seedance-2-0-fast-260128` | $3.30/M tokens |

---

## Cost Tracker Warnings

| Symptom | Likely cause | What to do |
|---------|-------------|------------|
| `WARNING: cost tracker is per-worker only` in logs | Running with `WORKERS > 1` | The in-memory cost tracker doesn't aggregate across worker processes. Use an external store (Redis, Postgres) or set `WORKERS=1` for accurate totals |
| Cost totals reset on restart | In-memory persistence | This is expected. For durable cost tracking, set `PERSISTENCE_BACKEND=postgres` and configure a database |
| Cost per SKU seems high | Routing all to Pro tier + safety + quality evals | Each SKU costs: script gen (Seed 1.8) + safety eval (Seed 1.8) + quality eval (Seed 1.8) + video gen (Seedance). Check `GET /metrics` for breakdown |

---

## Pipeline Setup

| Symptom | Likely cause | What to do |
|---------|-------------|------------|
| `ValidationError` on startup | Required env vars missing | Run `python -c "from app.config import settings; print('OK')"` — it will show which fields failed |
| `dry_run=true` but API is still called | Module imported before `dry_run` check | `dry_run` mode disables video generation only. Safety and quality evals still call Seed 1.8. To skip all API calls, also set `SAFETY_ENABLED=false` and `QUALITY_EVAL_ENABLED=false` |
| Output videos not saved | `output_dir` not writable | Check `OUTPUT_DIR` in `.env`; directory is created on startup if missing |
| Batch job hangs silently | `BATCH_CONCURRENCY_DEFAULT` set too high + API rate limiting | Lower concurrency; check logs for `429` errors being retried |
