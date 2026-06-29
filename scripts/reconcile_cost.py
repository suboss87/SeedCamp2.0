#!/usr/bin/env python3
"""
Cost reconciliation harness.

WHY THIS EXISTS
---------------
SeedCamp's headline promise is *transparent, predictable per-video cost*. That
promise is only credible if the number the code computes matches (a) what the
docs claim and (b) what BytePlus ModelArk actually bills.

This script prints the per-video cost the shipped `cost_tracker` computes for a
matrix of tier / resolution / duration combinations, using the real token
formula and price constants from `app/config.py`. Run it, compare the output to
your actual ModelArk invoice for the same settings, and reconcile any gap before
publishing cost figures.

It does NOT call any API and costs nothing to run.

Usage:
    python3 scripts/reconcile_cost.py
    python3 scripts/reconcile_cost.py --invoice-per-video 0.04   # flag docs vs reality
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.models.schemas import SKUTier  # noqa: E402
from app.services.cost_tracker import calculate_cost  # noqa: E402
from app.services.pipeline import _estimate_video_tokens  # noqa: E402

# Documented per-video claims that this harness guards against drift.
# Update these ONLY after validating against a real invoice.
DOCUMENTED_CLAIMS = {
    "README ($/video)": (0.08, 0.13),
    "market-research Fast 10s ($/video)": (0.03, 0.04),
}

# Representative script token usage (Seed 1.8) for a single generation.
# These mirror the dry-run stub so the totals are comparable.
SCRIPT_IN_TOKENS = 450
SCRIPT_OUT_TOKENS = 180

MATRIX = [
    (SKUTier.catalog, "480p", 5),
    (SKUTier.catalog, "720p", 8),
    (SKUTier.hero, "720p", 8),
    (SKUTier.hero, "1080p", 8),
]


def _price_for(tier: SKUTier) -> float:
    return (
        settings.cost_per_m_seedance_pro
        if tier == SKUTier.hero
        else settings.cost_per_m_seedance_fast
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--invoice-per-video",
        type=float,
        default=None,
        help="Actual $/video from your ModelArk invoice, to compare against computed cost.",
    )
    args = parser.parse_args()

    print("=" * 78)
    print("SeedCamp cost reconciliation -- computed from app/config.py token model")
    print("=" * 78)
    print(
        f"Token formula: (w*h*fps*duration)/1024   "
        f"Seed1.8 in=${settings.cost_per_m_seed18_input}/M out=${settings.cost_per_m_seed18_output}/M"
    )
    print(
        f"Video price:  Standard ${settings.cost_per_m_seedance_pro}/M   "
        f"Fast ${settings.cost_per_m_seedance_fast}/M\n"
    )
    print(f"{'tier':8} {'res':6} {'dur':>4}  {'video_tokens':>12}  {'video$':>9}  {'total$':>9}")
    print("-" * 78)

    computed = []
    for tier, res, dur in MATRIX:
        tokens = _estimate_video_tokens(dur, res)
        model_id = settings.video_model_pro if tier == SKUTier.hero else settings.video_model_fast
        cost = calculate_cost(
            script_input_tokens=SCRIPT_IN_TOKENS,
            script_output_tokens=SCRIPT_OUT_TOKENS,
            video_tokens=tokens,
            model_used=model_id,
            cost_per_m=_price_for(tier),
            sku_tier=tier,
        )
        computed.append(cost.total_cost_usd)
        print(
            f"{tier.value:8} {res:6} {dur:>3}s  {tokens:>12,}  "
            f"${cost.video_cost_usd:>8.4f}  ${cost.total_cost_usd:>8.4f}"
        )

    lo, hi = min(computed), max(computed)
    print("-" * 78)
    print(f"Computed per-video range: ${lo:.4f} - ${hi:.4f}\n")

    print("Documented claims (must match a real invoice before you publish them):")
    drift = False
    for label, (clo, chi) in DOCUMENTED_CLAIMS.items():
        overlap = not (hi < clo or lo > chi)
        flag = "OK" if overlap else "MISMATCH"
        if not overlap:
            drift = True
        print(f"  [{flag:8}] {label}: ${clo}-${chi}  vs computed ${lo:.4f}-${hi:.4f}")

    if args.invoice_per_video is not None:
        inv = args.invoice_per_video
        print(f"\nReal invoice supplied: ${inv:.4f}/video")
        nearest = min(computed, key=lambda c: abs(c - inv))
        ratio = nearest / inv if inv else float("inf")
        print(
            f"  Nearest computed: ${nearest:.4f}  =>  code is {ratio:.1f}x the invoice. "
            f"{'FIX the token formula / price constants.' if abs(ratio - 1) > 0.2 else 'Within tolerance.'}"
        )

    if drift:
        print(
            "\n>>> ACTION: computed cost does not overlap the documented claims. "
            "Either the token formula/price in config.py is wrong, or the docs are. "
            "Validate against a real ModelArk invoice and reconcile both."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
