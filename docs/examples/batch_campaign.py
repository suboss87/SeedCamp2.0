"""
Create a campaign, upload products via CSV, and trigger batch generation.

Usage:
    # Start the API first (with Firestore configured)
    make dev

    # Run this script
    python3 docs/examples/batch_campaign.py
"""
import asyncio
import httpx

API_URL = "http://localhost:8000"
CSV_PATH = "tests/fixtures/sample_products.csv"


async def main():
    async with httpx.AsyncClient(timeout=60) as client:
        # Step 1: Create campaign
        print("Creating campaign...")
        resp = await client.post(
            f"{API_URL}/api/campaigns/",
            json={
                "name": "Summer Launch 2026",
                "theme": "Energetic summer vibes with bright colors and upbeat music",
                "platforms": ["tiktok", "instagram"],
                "duration": 8,
            },
        )
        resp.raise_for_status()
        campaign = resp.json()
        campaign_id = campaign["id"]
        print(f"Campaign created: {campaign_id}")

        # Step 2: Upload product CSV
        print("\nUploading product catalog...")
        with open(CSV_PATH, "rb") as f:
            resp = await client.post(
                f"{API_URL}/api/campaigns/{campaign_id}/products",
                files={"file": ("products.csv", f, "text/csv")},
            )
        resp.raise_for_status()
        upload = resp.json()
        print(f"Products created: {upload['products_created']}, skipped: {upload['products_skipped']}")

        # Step 3: Start batch generation
        print("\nStarting batch generation (concurrency=2)...")
        resp = await client.post(
            f"{API_URL}/api/campaigns/{campaign_id}/generate",
            json={"concurrency": 2},
        )
        resp.raise_for_status()
        print("Batch generation started!")

        # Step 4: Poll progress
        print("\nPolling progress...")
        for _ in range(120):
            resp = await client.get(f"{API_URL}/api/campaigns/{campaign_id}/progress")
            progress = resp.json()

            completed = progress["completed_videos"]
            total = progress["total_products"]
            pct = progress["progress_pct"]
            print(f"  {completed}/{total} complete ({pct:.0f}%) -- ${progress['total_cost_usd']:.3f}")

            if progress["status"] in ("completed", "partial", "failed"):
                print(f"\nFinal status: {progress['status']}")
                break

            await asyncio.sleep(10)

        # Step 5: View results
        resp = await client.get(f"{API_URL}/api/campaigns/{campaign_id}")
        final = resp.json()
        print(f"\nCampaign: {final['name']}")
        print(f"Total cost: ${final['total_cost_usd']:.3f}")
        print(f"Completed: {final['completed_videos']}/{final['total_products']}")


if __name__ == "__main__":
    asyncio.run(main())
