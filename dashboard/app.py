"""
D2C Video Ad Pipeline — Streamlit Dashboard
POC frontend matching the Solution Brief architecture.
"""
import time

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="D2C Video Ad Pipeline", page_icon="🎬", layout="wide")

st.title("🎬 D2C Video Ad Pipeline")
st.caption("AI-Powered Product Video Generation at Scale · BytePlus ModelArk POC")

# ─── Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Pipeline Config")
    sku_tier = st.selectbox("SKU Tier", ["catalog", "hero"], index=0,
                            help="Hero (top 20%): Seedance Pro · Catalog (80%): Pro Fast")
    resolution = st.selectbox("Resolution", ["720p", "1080p", "480p"])
    duration = st.slider("Duration (seconds)", 2, 12, 8)
    platforms = st.multiselect("Target Platforms",
                               ["tiktok", "instagram", "youtube"],
                               default=["tiktok"])

    st.divider()
    st.markdown("### Pipeline Architecture")
    st.markdown("""
    1. **INPUT** → Brief + Image + SKU Tier
    2. **SEED 1.8** → Script generation
    3. **MODEL ROUTER** → Smart routing
    4. **SEEDANCE** → Video generation
    5. **FFMPEG** → Platform formatting
    6. **OUTPUT** → Platform-ready assets
    """)

    st.divider()
    st.markdown("### Smart Model Routing")
    st.markdown("""
    - **Hero SKUs** → Seedance 1.5 Pro ($1.20/M)
    - **Catalog SKUs** → Pro Fast ($0.70/M)
    """)

# ─── Main Form ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    brief = st.text_area(
        "📝 Campaign Brief",
        placeholder="e.g. Summer collection launch, beach vibes, young audience, energetic mood...",
        height=120,
    )
    sku_id = st.text_input("🏷️ SKU ID", value="SKU-001")

with col2:
    image_url = st.text_input(
        "🖼️ Product Image URL (optional)",
        placeholder="https://example.com/product.jpg",
    )
    if image_url:
        st.image(image_url, width=200)

# ─── Generate ─────────────────────────────────────────────────────────────────────
if st.button("🚀 Generate Video Ad", type="primary", use_container_width=True):
    if not brief:
        st.error("Please enter a campaign brief.")
        st.stop()

    payload = {
        "brief": brief,
        "product_image_url": image_url or None,
        "sku_tier": sku_tier,
        "sku_id": sku_id,
        "platforms": platforms,
        "duration": duration,
        "resolution": resolution,
    }

    # Steps 1-4: Start pipeline
    with st.spinner("🧠 Running D2C pipeline: Script → Route → Video..."):
        try:
            resp = requests.post(f"{API_BASE}/api/generate", json=payload, timeout=120)
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            st.error(f"Pipeline Error: {e}")
            st.stop()

    # Show script output
    st.subheader("✨ Generated Ad Script (Seed 1.8)")
    script = result.get("script", {})
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Ad Copy:** {script.get('ad_copy', '')}")
        st.markdown(f"**Scene:** {script.get('scene_description', '')}")
    with col_b:
        st.markdown(f"**Camera:** {script.get('camera_direction', '')}")
        with st.expander("Full Video Prompt"):
            st.code(script.get("video_prompt", ""), language=None)

    # Show routing decision
    st.subheader("🚦 Model Routing")
    video_info = result.get("video", {})
    cost_info = result.get("cost", {})
    tier_emoji = "🌟" if sku_tier == "hero" else "📦"
    st.info(f"{tier_emoji} **{sku_tier.upper()}** SKU → `{video_info.get('model_used', '')}` @ ${cost_info.get('cost_per_m_tokens', 0)}/M tokens")

    # Show cost breakdown
    st.subheader("💰 Cost Breakdown")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Script Cost", f"${cost_info.get('script_cost_usd', 0):.4f}")
    with c2:
        st.metric("Video Cost (est)", f"${cost_info.get('video_cost_usd', 0):.4f}")
    with c3:
        st.metric("Total Cost", f"${cost_info.get('total_cost_usd', 0):.4f}")

    # Poll for video
    task_id = result.get("task_id")
    if task_id:
        st.subheader("🎥 Video Generation")
        progress = st.progress(0, text="Waiting for video...")

        for i in range(60):  # max 5 minutes
            time.sleep(5)
            progress.progress(min((i + 1) * 3, 95), text=f"Generating video... ({(i+1)*5}s)")
            try:
                status_resp = requests.get(f"{API_BASE}/api/status/{task_id}", timeout=30)
                status_resp.raise_for_status()
                status = status_resp.json()
            except Exception:
                continue

            if status.get("status") == "Succeeded":
                progress.progress(100, text="✅ Video ready!")
                video_url = status.get("video_url")
                if video_url:
                    st.video(video_url)
                break

            elif status.get("status") == "Failed":
                progress.progress(100, text="❌ Generation failed")
                st.error(status.get("error", "Unknown error"))
                break
        else:
            st.warning("⏱️ Video generation timed out. Check /api/status/{task_id} later.")

# ─── Cost Summary ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📊 Cost Tracking — POC Metrics")
if st.button("🔄 Refresh Cost Summary"):
    try:
        cost_resp = requests.get(f"{API_BASE}/api/cost-summary", timeout=10)
        cost_resp.raise_for_status()
        summary = cost_resp.json()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Videos", summary.get("total_videos", 0))
        with c2:
            st.metric("Avg Cost/Video", f"${summary.get('avg_cost_per_video', 0):.4f}")
        with c3:
            st.metric("Hero Videos", summary.get("hero_videos", 0))
        with c4:
            st.metric("Catalog Videos", summary.get("catalog_videos", 0))

        st.caption(f"Total spend: ${summary.get('total_cost_usd', 0):.4f} | "
                   f"Target: $0.16/video (V2 Brief)")
    except Exception as e:
        st.error(f"Error: {e}")
