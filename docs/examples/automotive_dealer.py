"""
Automotive dealership example: generate videos for a vehicle inventory.

Demonstrates tiered routing for a dealership with 300+ vehicles:
  - Featured/certified vehicles -> Premium model (cinematic walkaround)
  - Bulk used inventory -> Fast model (quick showcase)

Usage:
    # Start the API first (DRY_RUN=true works without API keys)
    DRY_RUN=true make dev

    # Run this script
    python3 docs/examples/automotive_dealer.py
"""
import asyncio

import httpx

API_URL = "http://localhost:8000"

# Sample vehicle inventory -- a mix of featured and standard stock
VEHICLES = [
    {
        "brief": "2026 BMW X5 xDrive40i, Mineral White, panoramic roof, "
                 "Harman Kardon audio, 12.3-inch display. Certified Pre-Owned "
                 "with 5-year warranty. Target: luxury SUV buyers.",
        "sku_tier": "hero",
        "sku_id": "VIN-BMW-X5-2026-001",
        "platforms": ["youtube"],
        "duration": 8,
        "resolution": "1080p",
    },
    {
        "brief": "2025 Toyota Camry SE, Celestial Silver, 2.5L 4-cyl, "
                 "Toyota Safety Sense 3.0, Apple CarPlay. 28K miles, "
                 "one owner. Great commuter car.",
        "sku_tier": "catalog",
        "sku_id": "VIN-CAMRY-2025-047",
        "platforms": ["tiktok", "instagram"],
        "duration": 5,
        "resolution": "720p",
    },
    {
        "brief": "2026 Ford F-150 Lightning Platinum, Star White, "
                 "extended range battery 320mi, BlueCruise hands-free, "
                 "Pro Power Onboard 9.6kW. Featured truck of the month.",
        "sku_tier": "hero",
        "sku_id": "VIN-F150L-2026-003",
        "platforms": ["youtube", "tiktok"],
        "duration": 8,
        "resolution": "1080p",
    },
    {
        "brief": "2023 Honda Civic LX, Aegean Blue, 2.0L, 36 mpg highway, "
                 "Honda Sensing suite, 42K miles. Affordable and reliable.",
        "sku_tier": "catalog",
        "sku_id": "VIN-CIVIC-2023-112",
        "platforms": ["tiktok"],
        "duration": 5,
        "resolution": "720p",
    },
    {
        "brief": "2024 Chevrolet Tahoe RST, Black, 5.3L V8, magnetic ride "
                 "control, rear entertainment, tow package 8,200 lbs. "
                 "Family-ready full-size SUV.",
        "sku_tier": "catalog",
        "sku_id": "VIN-TAHOE-2024-089",
        "platforms": ["instagram"],
        "duration": 5,
        "resolution": "720p",
    },
]


async def main():
    total_cost = 0.0
    results = []

    async with httpx.AsyncClient(timeout=30) as client:
        for vehicle in VEHICLES:
            sku = vehicle["sku_id"]
            tier = vehicle["sku_tier"]
            print(f"[{tier.upper():>7}] Generating video for {sku}...")

            resp = await client.post(f"{API_URL}/api/generate", json=vehicle)
            resp.raise_for_status()
            data = resp.json()

            cost = data.get("cost", {}).get("total_cost_usd", 0)
            model = data.get("video", {}).get("model_used", "unknown")
            total_cost += cost

            results.append({
                "sku": sku,
                "tier": tier,
                "model": model,
                "cost": cost,
                "task_id": data["task_id"],
            })

            print(f"         Model: {model} | Cost: ${cost:.4f}")

    # Summary
    hero_count = sum(1 for r in results if r["tier"] == "hero")
    catalog_count = sum(1 for r in results if r["tier"] == "catalog")

    print(f"\n{'='*60}")
    print("Dealership Video Batch Complete")
    print(f"{'='*60}")
    print(f"  Featured vehicles (premium model): {hero_count}")
    print(f"  Standard inventory (fast model):   {catalog_count}")
    print(f"  Total cost:                        ${total_cost:.4f}")
    print(f"  Avg cost/vehicle:                  ${total_cost/len(results):.4f}")
    print("\nAt 300 vehicles/lot with 20% featured:")
    projected = (300 * 0.20 * 0.13) + (300 * 0.80 * 0.08)
    print(f"  Projected lot cost: ${projected:.2f}")
    print(f"  vs. studio video:   ${300 * 500:.0f} - ${300 * 2000:.0f}")


if __name__ == "__main__":
    asyncio.run(main())
