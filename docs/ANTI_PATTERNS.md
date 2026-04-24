# Anti-Patterns

Shortcuts that seem reasonable and consistently cause problems. Each one has been observed in real video pipeline deployments.

---

## Safety

**Disabling the safety evaluator to hit a deadline**

```bash
# Don't do this in production
SAFETY_ENABLED=false
```

The safety evaluator exists because BytePlus platform safety will reject the same content at generation time. Disabling it locally doesn't make the content safer — it just moves the failure from your evaluator (where you get a structured response and can fix it) to the BytePlus API (where you get a 4xx and a queued task that never completes). You spend more time debugging the API failure than it would have taken to fix the script.

**Use `SAFETY_ENABLED=false` only in local dry-run development. Never in production.**

---

**Lowering the block threshold to pass more scripts**

```bash
# Tempting when a product vertical keeps getting flagged
SAFETY_THRESHOLD_BLOCK=0.95  # raised from 0.8
```

If a product category consistently scores 0.85 on `brand_safety`, the signal is that the script writer is framing the product in a risky way. Raising the threshold papers over the signal. Fix the product brief or the script writer prompt instead. The threshold exists to catch things before they reach BytePlus — not to be tuned to fit your content.

---

## Routing

**Routing all SKUs to Pro to chase quality**

```python
# In your request loop — don't do this
GenerateRequest(sku_tier="hero", ...)  # for every SKU regardless of value
```

Quality gates exist so you don't need to use Pro for everything. Routing 100% to Pro costs 30% more than the 20/80 split and hits rate limits faster during batch jobs. If quality is consistently low on Catalog SKUs, the fix is the prompt — not the model tier.

**Route to Hero only for genuinely high-value SKUs — the top 20% by revenue contribution or campaign priority.**

---

**Adding a third tier by duplicating routing logic**

If two tiers aren't enough, extend `SKUTier` and `_ROUTES` in `app/services/model_router.py`. Don't copy the routing function or add conditional logic around it in `app/main.py` — that splits routing into two places and they will drift.

---

## Polling and Retries

**Reducing poll interval to finish faster**

```bash
POLL_INTERVAL=1  # changed from 5
```

Polling every 1 second instead of every 5 seconds doesn't make BytePlus generate the video faster. It burns 5x the API calls for status checks, which contributes to rate limit pressure on your account, and adds noise to logs. The video finishes when it finishes.

**Don't touch `POLL_INTERVAL` below 3 seconds. The default of 5s is already aggressive.**

---

**Swallowing retry exhaustion silently**

```python
try:
    result = await create_video_task(...)
except Exception:
    result = None  # "handle it later"
```

When all retries are exhausted, the exception carries the last error type and status code. Swallowing it loses the signal — you won't know if it was a rate limit (temporary, retry later), a quota error (fix account), or a bad prompt (fix content). Let the exception propagate and handle each type explicitly.

---

## Cost Tracking

**Running WORKERS > 1 and trusting `/metrics` totals**

The built-in cost tracker is per-process. With `WORKERS=4`, each worker tracks its own costs independently. The `/metrics` endpoint only reflects the costs seen by the worker that handled that request — not the total across all workers. You will undercount.

Either run `WORKERS=1` (works for most production loads) or use Prometheus to aggregate across workers. Never read raw `/metrics` in a multi-worker setup and treat it as ground truth.

---

## Configuration

**Hardcoding model IDs in request payloads**

```python
# Don't do this
payload = {"model": "dreamina-seedance-2-0-260128", ...}
```

Model IDs come from `settings.video_model_pro` and `settings.video_model_fast`. When BytePlus releases a new version, you update one line in `.env` — not every place a model ID appears. Hardcoded IDs will silently call a deprecated model after you've updated config.

---

**Committing `.env` to the repo**

`.env` is in `.gitignore`. If you're working from a fork and want to share config, copy `.env.example` and fill it in — never commit your actual key.

---

## Testing

**Writing tests that mock the BytePlus API and calling them "integration tests"**

Mocked API tests verify that your code calls the API with the right arguments. They don't verify that BytePlus accepts those arguments, returns the expected shape, or that your parsing of the response is correct. The test suite already separates unit tests (mocked) from integration tests (real API required). Don't move integration-level assertions into mocked unit tests — the distinction exists for a reason.

---

## General

**Forking and immediately removing the evaluators to "simplify"**

The safety and quality evaluators add 2-3 seconds per SKU and cost roughly $0.001 each. This feels like overhead until a batch of 200 SKUs produces content that gets flagged by BytePlus at generation time, or your client reviews the output and finds obvious quality issues. The evaluators are cheap insurance. Keep them.

**If you genuinely don't need them** (e.g., you control the prompts end-to-end and have a separate content review process), disable them via env vars rather than deleting the code — that way you can re-enable without a refactor.
