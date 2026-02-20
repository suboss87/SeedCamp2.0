"""
Generate a single product video via the AdCamp API.

Usage:
    # Start the API first
    make dev

    # Run this script
    python3 examples/generate_single_video.py
"""
import asyncio
import httpx

API_URL = "http://localhost:8000"


async def main():
    payload = {
        "brief": "Premium wireless headphones with active noise cancellation. "
                 "Target: young professionals. Tone: sleek and modern.",
        "sku_tier": "catalog",
        "sku_id": "SKU-HEADPHONES-001",
        "platforms": ["tiktok"],
        "duration": 5,
        "resolution": "720p",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Submit generation request
        print("Submitting generation request...")
        resp = await client.post(f"{API_URL}/api/generate", json=payload)
        resp.raise_for_status()
        result = resp.json()

        task_id = result["task_id"]
        print(f"Task created: {task_id}")
        print(f"Model used: {result['video']['model_used']}")
        print(f"Script headline: {result['script']['headline']}")

        # Step 2: Poll until complete
        print("\nPolling for video completion...")
        for _ in range(60):
            status_resp = await client.get(f"{API_URL}/api/status/{task_id}")
            status = status_resp.json()

            if status["status"] == "Succeeded":
                print(f"\nVideo ready: {status['video_url']}")
                return
            elif status["status"] == "Failed":
                print(f"\nGeneration failed: {status.get('error')}")
                return

            print(f"  Status: {status['status']}...")
            await asyncio.sleep(5)

        print("\nTimed out waiting for video.")


if __name__ == "__main__":
    asyncio.run(main())
