#!/usr/bin/env python3
"""
Real-API smoke test (the one test the 139-test suite does NOT cover).

WHY THIS EXISTS
---------------
Every test in `tests/` runs in DRY_RUN with simulated responses. Nothing in CI
ever calls ModelArk. That means three launch-critical unknowns are unverified:

  1. Do the configured model IDs (dreamina-seedance-2-0-*) actually resolve?
  2. Does the live request/response shape match what `video_gen.py` expects?
  3. What does a real generation actually cost (feeds scripts/reconcile_cost.py)?

This script runs ONE real hero + ONE real catalog generation end to end against
the live API, polls to completion, and prints the resolved model, the returned
video URL, wall-clock time, and the computed cost. Treat a green run here as the
gate for a public release.

Requirements:
    export ARK_API_KEY=...        # a real BytePlus ModelArk key
    DRY_RUN must be unset/false   # this is a REAL call and WILL incur cost

Usage:
    ARK_API_KEY=... python3 scripts/smoke_test.py
    ARK_API_KEY=... python3 scripts/smoke_test.py --tier hero --resolution 1080p
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.models.schemas import SKUTier  # noqa: E402


async def _run_one(tier: SKUTier, resolution: str, duration: int) -> bool:
    # Imported lazily so a missing key / dry-run misconfig fails loudly here.
    from app.services import video_gen
    from app.services.pipeline import run_pipeline

    label = f"{tier.value}/{resolution}/{duration}s"
    print(f"\n=== Smoke test: {label} ===")
    t0 = time.time()
    try:
        result = await run_pipeline(
            brief="A premium product on a reflective surface, cinematic studio lighting, slow dolly-in",
            sku_tier=tier,
            sku_id=f"SMOKE-{tier.value.upper()}",
            duration=duration,
            resolution=resolution,
        )
    except Exception as exc:  # noqa: BLE001 -- smoke test surfaces any failure
        print(f"  FAIL: pipeline raised before video task: {type(exc).__name__}: {exc}")
        print("  -> Check ARK_API_KEY, model IDs in config.py, and the request payload.")
        return False

    model_id = result["model_id"]
    task_id = result["task_id"]
    print(f"  model resolved: {model_id}")
    print(f"  task created:   {task_id}")

    status = await video_gen.wait_for_video(task_id, model_id)
    elapsed = time.time() - t0

    print(f"  status:         {status.status}  ({elapsed:.0f}s)")
    if status.status != "Succeeded":
        print(f"  FAIL: {status.error or status.status}")
        return False

    print(f"  video_url:      {status.video_url}")
    print(f"  computed cost:  ${result['cost'].total_cost_usd:.4f}")
    print(
        "  -> Compare this cost to your ModelArk invoice; run scripts/reconcile_cost.py "
        f"--invoice-per-video <actual> to validate the ${result['cost'].total_cost_usd:.4f} figure."
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=["hero", "catalog", "both"], default="both")
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--duration", type=int, default=8)
    args = parser.parse_args()

    if settings.dry_run:
        print("ERROR: DRY_RUN is enabled. This smoke test must hit the real API. Unset DRY_RUN.")
        sys.exit(2)
    if not settings.ark_api_key:
        print("ERROR: ARK_API_KEY is not set. Export a real BytePlus ModelArk key.")
        sys.exit(2)

    tiers = (
        [SKUTier.hero, SKUTier.catalog]
        if args.tier == "both"
        else [SKUTier(args.tier)]
    )
    ok = all(asyncio.run(_run_one(t, args.resolution, args.duration)) for t in tiers)

    print("\n" + ("ALL SMOKE TESTS PASSED -- safe to launch the happy path." if ok else "SMOKE TEST FAILED -- do not launch until fixed."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
