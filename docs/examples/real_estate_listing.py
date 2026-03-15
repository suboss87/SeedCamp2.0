"""
Real estate listing example: generate videos for property listings.

Demonstrates tiered routing for an agency with 500+ listings:
  - Luxury listings ($1M+) -> Premium model (cinematic walkthrough)
  - Standard listings -> Fast model (quick virtual tour)

Only 9% of agents currently make listing videos, despite listings with
video receiving 403% more inquiries. SeedCamp makes it economical to
create video for every listing.

Usage:
    # Start the API first (DRY_RUN=true works without API keys)
    DRY_RUN=true make dev

    # Run this script
    python3 docs/examples/real_estate_listing.py
"""
import asyncio
import httpx

API_URL = "http://localhost:8000"

# Sample property listings -- mix of luxury and standard
LISTINGS = [
    {
        "brief": "Luxury waterfront estate, 5BR/6BA, 6,200 sqft on 1.2 acres. "
                 "Private dock, infinity pool, chef's kitchen with Sub-Zero and Wolf. "
                 "Floor-to-ceiling windows with panoramic bay views. $3.2M. "
                 "Tone: aspirational, cinematic.",
        "sku_tier": "hero",
        "sku_id": "MLS-2026-WF-4521",
        "platforms": ["youtube"],
        "duration": 8,
        "resolution": "1080p",
    },
    {
        "brief": "Modern 2BR/2BA condo, 1,100 sqft, 8th floor with city views. "
                 "Updated kitchen, in-unit laundry, one parking spot. "
                 "Walk to metro. $425K. Great starter home.",
        "sku_tier": "catalog",
        "sku_id": "MLS-2026-CD-7833",
        "platforms": ["tiktok", "instagram"],
        "duration": 5,
        "resolution": "720p",
    },
    {
        "brief": "Historic Victorian, 4BR/3BA, 3,400 sqft. Original hardwood floors, "
                 "crown molding, updated systems. Wraparound porch, detached carriage "
                 "house. $1.8M. Heritage district. Tone: elegant, timeless.",
        "sku_tier": "hero",
        "sku_id": "MLS-2026-VIC-1205",
        "platforms": ["youtube", "instagram"],
        "duration": 8,
        "resolution": "1080p",
    },
    {
        "brief": "3BR/2BA ranch, 1,600 sqft, open floor plan. New roof 2025, "
                 "fenced backyard, attached 2-car garage. Good school district. "
                 "$340K. Family-friendly neighborhood.",
        "sku_tier": "catalog",
        "sku_id": "MLS-2026-RN-9041",
        "platforms": ["tiktok"],
        "duration": 5,
        "resolution": "720p",
    },
    {
        "brief": "1BR/1BA apartment, 650 sqft, renovated bathroom, new appliances. "
                 "Laundry in building, street parking. Near downtown. "
                 "$1,200/mo rental listing.",
        "sku_tier": "catalog",
        "sku_id": "MLS-2026-APT-3376",
        "platforms": ["tiktok"],
        "duration": 5,
        "resolution": "720p",
    },
]


async def main():
    total_cost = 0.0
    results = []

    async with httpx.AsyncClient(timeout=30) as client:
        for listing in LISTINGS:
            mls = listing["sku_id"]
            tier = listing["sku_tier"]
            print(f"[{tier.upper():>7}] Generating video for {mls}...")

            resp = await client.post(f"{API_URL}/api/generate", json=listing)
            resp.raise_for_status()
            data = resp.json()

            cost = data.get("cost", {}).get("total_cost_usd", 0)
            model = data.get("video", {}).get("model_used", "unknown")
            total_cost += cost

            results.append({
                "mls": mls,
                "tier": tier,
                "model": model,
                "cost": cost,
                "task_id": data["task_id"],
            })

            print(f"         Model: {model} | Cost: ${cost:.4f}")

    # Summary
    luxury_count = sum(1 for r in results if r["tier"] == "hero")
    standard_count = sum(1 for r in results if r["tier"] == "catalog")

    print(f"\n{'='*60}")
    print(f"Real Estate Listing Batch Complete")
    print(f"{'='*60}")
    print(f"  Luxury listings (premium model):   {luxury_count}")
    print(f"  Standard listings (fast model):    {standard_count}")
    print(f"  Total cost:                        ${total_cost:.4f}")
    print(f"  Avg cost/listing:                  ${total_cost/len(results):.4f}")
    print(f"\nAt agency scale (200 active listings, 15% luxury):")
    luxury_cost = 200 * 0.15 * 0.13
    standard_cost = 200 * 0.85 * 0.08
    print(f"  Cost per refresh:   ${luxury_cost + standard_cost:.2f}")
    print(f"  vs. traditional:    ${200 * 300:.0f} - ${200 * 500:.0f}")
    print(f"\n  Listings with video get 403% more inquiries.")
    print(f"  Only 9% of agents currently make listing videos.")
    print(f"  SeedCamp makes full-inventory video coverage economical.")


if __name__ == "__main__":
    asyncio.run(main())
