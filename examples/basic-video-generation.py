#!/usr/bin/env python3
"""
Basic Video Generation Example

Demonstrates the simplest way to generate a single video using the AdCamp API.
"""

import requests
import json
import sys

# API endpoint (update with your deployed URL)
API_URL = "http://localhost:8000"

def generate_video(product_name: str, sku_tier: str = "catalog"):
    """Generate a single video for a product"""
    
    endpoint = f"{API_URL}/api/v1/campaigns/generate"
    
    payload = {
        "product_name": product_name,
        "key_features": ["High Quality", "Best Value", "Fast Shipping"],
        "target_audience": "General consumers",
        "tone": "Professional and friendly",
        "cta": "Shop Now",
        "sku_tier": sku_tier  # "hero" or "catalog"
    }
    
    print(f"🎬 Generating video for: {product_name} (tier: {sku_tier})")
    print(f"📡 Sending request to: {endpoint}")
    
    try:
        response = requests.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n✅ Video generated successfully!")
        print(f"📹 Video URL: {result['video_url']}")
        print(f"📝 Script: {result['script'][:100]}...")
        print(f"⏱️  Generation time: {result['generation_time_seconds']:.2f}s")
        print(f"💰 Cost: ${result['cost']:.4f}")
        print(f"🤖 Model used: {result['model_used']}")
        
        return result
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Video generation may take up to 60 seconds.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"   {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def main():
    # Example 1: Generate a catalog video (default tier)
    print("=" * 60)
    print("Example 1: Catalog SKU (Standard Video)")
    print("=" * 60)
    generate_video("Premium Coffee Beans", sku_tier="catalog")
    
    print("\n" + "=" * 60)
    print("Example 2: Hero SKU (High-Quality Video)")
    print("=" * 60)
    generate_video("Limited Edition Espresso Machine", sku_tier="hero")


if __name__ == "__main__":
    main()
