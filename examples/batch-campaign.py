#!/usr/bin/env python3
"""
Batch Campaign Generation Example

Demonstrates how to generate multiple videos for a product catalog efficiently.
Uses asyncio for concurrent requests with rate limiting.
"""

import requests
import asyncio
import aiohttp
from typing import List, Dict
import json

API_URL = "http://localhost:8000"
MAX_CONCURRENT = 5  # Match API rate limit

# Sample product catalog
PRODUCT_CATALOG = [
    {"name": "Organic Dark Roast Coffee", "tier": "catalog", "features": ["Organic", "Fair Trade", "Bold Flavor"]},
    {"name": "Limited Edition Espresso Machine", "tier": "hero", "features": ["Premium Build", "Smart Controls", "2-Year Warranty"]},
    {"name": "Stainless Steel French Press", "tier": "catalog", "features": ["Durable", "Easy Clean", "1L Capacity"]},
    {"name": "Artisan Coffee Grinder", "tier": "hero", "features": ["Precision Grinding", "15 Settings", "Quiet Motor"]},
    {"name": "Ceramic Coffee Mug Set", "tier": "catalog", "features": ["Dishwasher Safe", "4-Piece Set", "Modern Design"]},
]


async def generate_video_async(session: aiohttp.ClientSession, product: Dict) -> Dict:
    """Generate a single video asynchronously"""
    
    endpoint = f"{API_URL}/api/v1/campaigns/generate"
    
    payload = {
        "product_name": product["name"],
        "key_features": product["features"],
        "target_audience": "Coffee enthusiasts",
        "tone": "Warm and inviting",
        "cta": "Shop Now",
        "sku_tier": product["tier"]
    }
    
    print(f"📤 Generating video for: {product['name']} ({product['tier']})...")
    
    try:
        async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
            response.raise_for_status()
            result = await response.json()
            
            print(f"✅ {product['name']} - Generated in {result['generation_time_seconds']:.1f}s (${result['cost']:.4f})")
            
            return {
                "product": product["name"],
                "success": True,
                "video_url": result["video_url"],
                "cost": result["cost"],
                "model": result["model_used"]
            }
            
    except Exception as e:
        print(f"❌ {product['name']} - Failed: {str(e)}")
        return {
            "product": product["name"],
            "success": False,
            "error": str(e)
        }


async def generate_batch(products: List[Dict]) -> List[Dict]:
    """Generate videos for multiple products with rate limiting"""
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def limited_generate(session, product):
        async with semaphore:
            return await generate_video_async(session, product)
    
    async with aiohttp.ClientSession() as session:
        tasks = [limited_generate(session, product) for product in products]
        results = await asyncio.gather(*tasks)
    
    return results


def print_summary(results: List[Dict]):
    """Print campaign generation summary"""
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    total_cost = sum(r.get("cost", 0) for r in successful)
    
    print("\n" + "=" * 60)
    print("CAMPAIGN SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"💰 Total cost: ${total_cost:.4f}")
    
    if successful:
        print("\n📹 Generated Videos:")
        for result in successful:
            print(f"   - {result['product']}")
            print(f"     URL: {result['video_url']}")
            print(f"     Model: {result['model']}")
    
    if failed:
        print("\n❌ Failed Products:")
        for result in failed:
            print(f"   - {result['product']}: {result['error']}")


def main():
    print("🚀 Starting batch campaign generation...")
    print(f"📦 Products to generate: {len(PRODUCT_CATALOG)}")
    print(f"⚡ Max concurrent requests: {MAX_CONCURRENT}\n")
    
    # Run async batch generation
    results = asyncio.run(generate_batch(PRODUCT_CATALOG))
    
    # Print summary
    print_summary(results)
    
    # Save results to file
    with open("campaign_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: campaign_results.json")


if __name__ == "__main__":
    main()
