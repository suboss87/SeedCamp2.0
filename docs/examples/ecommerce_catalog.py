"""
E-commerce catalog example: generate videos for product SKUs.

Demonstrates tiered routing for a catalog with 1K-100K SKUs:
  - Hero products (top 20% by revenue) -> Premium model
  - Long-tail catalog -> Fast model (cost-optimized)

Usage:
    # Start the API first (DRY_RUN=true works without API keys)
    DRY_RUN=true make dev

    # Run this script
    python3 docs/examples/ecommerce_catalog.py
"""
import asyncio

import httpx

API_URL = "http://localhost:8000"

# Sample product catalog -- mix of hero and long-tail SKUs
PRODUCTS = [
    {
        "brief": "Wireless noise-cancelling headphones, matte black, 40hr battery, "
                 "spatial audio, premium carrying case. Best-seller, 4.8-star rating. "
                 "Target: young professionals. Tone: sleek and modern.",
        "sku_tier": "hero",
        "sku_id": "SKU-AUDIO-WH1000-BLK",
        "platforms": ["tiktok", "instagram"],
        "duration": 8,
        "resolution": "1080p",
    },
    {
        "brief": "Organic cotton crew-neck t-shirt, heather grey, relaxed fit. "
                 "Sustainably sourced, pre-shrunk, unisex sizing XS-3XL. "
                 "Everyday essential at an accessible price point.",
        "sku_tier": "catalog",
        "sku_id": "SKU-APPAREL-TEE-GRY-M",
        "platforms": ["tiktok"],
        "duration": 5,
        "resolution": "720p",
    },
    {
        "brief": "Smart home security camera, 2K resolution, night vision, "
                 "two-way audio, AI person detection, cloud + local storage. "
                 "Top seller in home security. Featured on homepage.",
        "sku_tier": "hero",
        "sku_id": "SKU-HOME-SECCAM-2K",
        "platforms": ["youtube", "tiktok"],
        "duration": 8,
        "resolution": "1080p",
    },
    {
        "brief": "Stainless steel water bottle, 32oz, double-wall vacuum insulated, "
                 "keeps drinks cold 24hr / hot 12hr. Available in 8 colors.",
        "sku_tier": "catalog",
        "sku_id": "SKU-KITCHEN-BOTTLE-32",
        "platforms": ["instagram"],
        "duration": 5,
        "resolution": "720p",
    },
    {
        "brief": "USB-C to Lightning cable, 6ft, MFi certified, braided nylon, "
                 "fast charging compatible. Bulk accessory for electronics section.",
        "sku_tier": "catalog",
        "sku_id": "SKU-ELEC-CABLE-USBC-6",
        "platforms": ["tiktok"],
        "duration": 5,
        "resolution": "720p",
    },
    {
        "brief": "Ergonomic office chair, mesh back, adjustable lumbar support, "
                 "4D armrests, 300lb capacity. Work-from-home essential. "
                 "Featured in 'Top Picks' collection.",
        "sku_tier": "hero",
        "sku_id": "SKU-FURN-CHAIR-ERGO",
        "platforms": ["youtube"],
        "duration": 8,
        "resolution": "1080p",
    },
]


async def main():
    total_cost = 0.0
    results = []

    async with httpx.AsyncClient(timeout=30) as client:
        for product in PRODUCTS:
            sku = product["sku_id"]
            tier = product["sku_tier"]
            print(f"[{tier.upper():>7}] Generating video for {sku}...")

            resp = await client.post(f"{API_URL}/api/generate", json=product)
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
    hero_cost = sum(r["cost"] for r in results if r["tier"] == "hero")
    catalog_cost = sum(r["cost"] for r in results if r["tier"] == "catalog")

    print(f"\n{'='*60}")
    print("E-Commerce Catalog Batch Complete")
    print(f"{'='*60}")
    print(f"  Hero products (premium model):  {hero_count}  (${hero_cost:.4f})")
    print(f"  Catalog items (fast model):     {catalog_count}  (${catalog_cost:.4f})")
    print(f"  Total cost:                     ${total_cost:.4f}")
    print(f"  Avg cost/SKU:                   ${total_cost/len(results):.4f}")
    print("\nAt scale (5,000 SKUs, 20% hero, quarterly refresh):")
    annual_videos = 5000 * 4
    hero_annual = annual_videos * 0.20 * 0.13
    catalog_annual = annual_videos * 0.80 * 0.08
    print(f"  Annual videos:  {annual_videos:,}")
    print(f"  Annual cost:    ${hero_annual + catalog_annual:,.0f}")
    print(f"  vs. studio:     ${annual_videos * 500:,.0f} - ${annual_videos * 2000:,.0f}")


if __name__ == "__main__":
    asyncio.run(main())
