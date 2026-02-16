"""
AdCamp - AI Video Ad Generation Dashboard
Powered by BytePlus ModelArk
"""
import base64
import io
import json
import os
import time
from typing import Optional

import requests
import streamlit as st
from PIL import Image

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

API_BASE = os.getenv(
    "API_URL", 
    "https://adcamp-api-309502792454.asia-southeast1.run.app"
)

# BytePlus Brand Colors
BYTEPLUS_BLUE = "#0066FF"

# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_step_icon(status):
    """Get icon for step status."""
    if status == 'running':
        return "⏳"
    elif status == 'complete':
        return "✅"
    elif status == 'failed':
        return "❌"
    else:
        return "⚪"

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AdCamp · BytePlus ModelArk",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS with BytePlus branding
st.markdown(f"""
<style>
    /* BytePlus Blue throughout */
    .block-container {{
        padding-top: 1rem;
        max-width: 1400px;
    }}
    
    /* Header with logo */
    .header-container {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}
    
    .header-logo {{
        width: 48px;
        height: 48px;
    }}
    
    .header-title {{
        font-size: 2rem;
        font-weight: 700;
        color: {BYTEPLUS_BLUE};
        margin: 0;
    }}
    
    .header-subtitle {{
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 0.25rem;
    }}
    
    /* Progress step cards */
    .progress-step {{
        background: #ffffff;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        transition: all 0.3s ease;
    }}
    
    .progress-step.running {{
        border-color: {BYTEPLUS_BLUE};
        background: #eff6ff;
    }}
    
    .progress-step.complete {{
        border-color: #10b981;
        background: #f0fdf4;
    }}
    
    .progress-step.failed {{
        border-color: #ef4444;
        background: #fef2f2;
    }}
    
    .step-icon {{
        font-size: 1.5rem;
        min-width: 40px;
        text-align: center;
    }}
    
    .step-message {{
        font-size: 0.95rem;
        font-weight: 500;
        color: #374151;
    }}
    
    /* Video result card */
    .video-result {{
        background: #ffffff;
        border: 2px solid {BYTEPLUS_BLUE};
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1.5rem;
    }}
    
    /* Buttons with BytePlus blue */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
    }}
    
    .stButton > button[kind="primary"] {{
        background-color: {BYTEPLUS_BLUE} !important;
        border-color: {BYTEPLUS_BLUE} !important;
    }}
    
    /* Image preview */
    .image-preview {{
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.5rem;
        background: #f9fafb;
    }}
    
    /* Clean up defaults */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Cost badges */
    .cost-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 600;
        background: {BYTEPLUS_BLUE}15;
        color: {BYTEPLUS_BLUE};
    }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER WITH BYTEPLUS LOGO
# ═══════════════════════════════════════════════════════════════════════════════

col_logo, col_title = st.columns([1, 11])

with col_logo:
    # BytePlus logo (using styled box with icon)
    st.markdown(f"""
    <div style="width: 48px; height: 48px; background: linear-gradient(135deg, {BYTEPLUS_BLUE} 0%, #0052CC 100%); 
                border-radius: 8px; display: flex; align-items: center; 
                justify-content: center; font-size: 1.5rem; color: white; box-shadow: 0 2px 8px rgba(0, 102, 255, 0.3);">
        🎬
    </div>
    """, unsafe_allow_html=True)

with col_title:
    st.markdown(f"""
    <div>
        <h1 style="color: {BYTEPLUS_BLUE}; margin: 0; font-size: 2rem; font-weight: 700;">AdCamp</h1>
        <p style="color: #6b7280; margin: 0.25rem 0 0 0; font-size: 0.95rem;">
            AI Video Ad Generation · Powered by <strong style="color: {BYTEPLUS_BLUE};">BytePlus ModelArk</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR - SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    sku_tier = st.selectbox(
        "SKU Tier",
        ["catalog", "hero"],
        index=0,
        format_func=lambda x: f"🌟 Hero (Premium)" if x == "hero" else "📦 Catalog (Optimized)"
    )
    
    st.markdown(f"""
    <span class="cost-badge">
        {'$0.13/video' if sku_tier == 'hero' else '$0.08/video'}
    </span>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    resolution = st.select_slider(
        "Resolution",
        options=["480p", "720p", "1080p"],
        value="720p"
    )
    
    duration = st.slider(
        "Duration (sec)",
        2, 15, 8
    )
    
    platforms = st.multiselect(
        "Platforms",
        ["tiktok", "instagram", "youtube"],
        default=["tiktok"],
        format_func=lambda x: {"tiktok": "📱 TikTok", "instagram": "📷 Instagram", "youtube": "▶️ YouTube"}[x]
    )
    
    st.markdown("---")
    st.caption("💡 **Tip**: Hero tier uses Seedance 1.5 Pro for top SKUs")

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT - TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab1, tab2 = st.tabs(["🎬 Generate Video", "📊 Analytics"])

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1: VIDEO GENERATION
# ─────────────────────────────────────────────────────────────────────────────

with tab1:
    col_left, col_right = st.columns([2, 1], gap="large")
    
    with col_left:
        st.markdown("### 📝 Campaign Details")
        
        brief = st.text_area(
            "Campaign Brief",
            placeholder="Example: Summer collection launch featuring lightweight running shoes. Target audience: active millennials (25-35). Mood: energetic, aspirational. Setting: sunrise beach run with golden hour lighting. Key message: performance meets style.",
            height=150,
            help="Describe your campaign vision, target audience, mood, and key message"
        )
        
        col_a, col_b = st.columns(2)
        with col_a:
            sku_id = st.text_input(
                "SKU ID",
                value="SKU-001",
                placeholder="e.g., SHOE-RUN-2024-001"
            )
        with col_b:
            campaign_name = st.text_input(
                "Campaign Name",
                placeholder="e.g., Summer Sprint 2024",
                help="Internal reference name"
            )
    
    with col_right:
        st.markdown("### 🖼️ Product Image")
        
        uploaded_file = st.file_uploader(
            "Upload Product Image",
            type=["jpg", "jpeg", "png"],
            help="Min height: 300px. Optional but improves video quality.",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Product Preview", use_container_width=True)
            
            # Check dimensions
            width, height = image.size
            if height < 300:
                st.warning(f"⚠️ Image height ({height}px) is below recommended 300px minimum")
            else:
                st.success(f"✓ Image loaded ({width}×{height}px)")
        else:
            st.info("💡 **Pro Tip**: Adding a product image improves video relevance and quality")
    
    st.divider()
    
    # Generate button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_btn = st.button(
            "🚀 Generate Video Ad",
            type="primary",
            use_container_width=True,
            disabled=not brief
        )
    
    if not brief and generate_btn:
        st.error("⚠️ Please enter a campaign brief to continue")
    
    # ─── GENERATION FLOW WITH SSE ───
    if generate_btn and brief:
        # Prepare image (convert to URL or base64 if uploaded)
        image_url = None
        if uploaded_file:
            # For now, we'll skip image upload and use URL only
            # In production, you'd upload to S3/GCS and get URL
            st.warning("🚧 Image upload to be implemented - using text-only generation for now")
            image_url = None
        
        payload = {
            "brief": brief,
            "product_image_url": image_url,
            "sku_tier": sku_tier,
            "sku_id": sku_id,
            "platforms": platforms,
            "duration": duration,
            "resolution": resolution,
        }
        
        # Progress containers
        progress_container = st.container()
        script_container = st.container()
        cost_container = st.container()
        video_container = st.container()
        
        # Connect to SSE endpoint
        with progress_container:
            st.markdown("### 🔄 Generation Progress")
            
            progress_bar = st.progress(0)
            
            # Step status placeholders
            step_placeholders = {
                1: st.empty(),
                2: st.empty(),
                3: st.empty(),
                4: st.empty(),
                5: st.empty(),
            }
            
            try:
                response = requests.post(
                    f"{API_BASE}/api/generate-stream",
                    json=payload,
                    stream=True,
                    timeout=360
                )
                
                final_data = {}
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            
                            step = data.get('step')
                            status = data.get('status')
                            message = data.get('message', '')
                            progress = data.get('progress', 0)
                            
                            # Update progress bar
                            progress_bar.progress(progress / 100)
                            
                            # Update step status
                            if step and step in step_placeholders:
                                css_class = status if status in ['running', 'complete', 'failed'] else ''
                                icon = _get_step_icon(status)
                                step_placeholders[step].markdown(f"""
                                <div class="progress-step {css_class}">
                                    <div class="step-icon">{icon}</div>
                                    <div class="step-message">{message}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Store final data
                            if 'data' in data:
                                final_data.update(data['data'])
                            
                            # Check for completion or error
                            if status == 'complete' and step == 5:
                                break
                            elif status in ['failed', 'error', 'timeout']:
                                st.error(f"❌ {message}")
                                st.stop()
                
                # Show script
                with script_container:
                    st.divider()
                    if 'script' in final_data:
                        script_data = final_data['script']
                        with st.expander("📝 View Generated Script", expanded=False):
                            st.write("**Ad Copy:**", script_data.get('ad_copy', 'N/A'))
                            st.caption(script_data.get('scene_description', ''))
                
                # Show cost
                with cost_container:
                    if 'cost' in final_data:
                        cost_data = final_data['cost']
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Script Cost", f"${cost_data.get('script_cost_usd', 0):.4f}")
                        with col2:
                            st.metric("Video Cost", f"${cost_data.get('video_cost_usd', 0):.4f}")
                        with col3:
                            st.metric("Total Cost", f"${cost_data.get('total_cost_usd', 0):.4f}")
                
                # Show video
                with video_container:
                    st.divider()
                    if 'video_url' in final_data:
                        st.markdown(f"""
                        <div class="video-result">
                            <h3 style="color: {BYTEPLUS_BLUE}; margin-top: 0;">✅ Video Generated Successfully!</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.video(final_data['video_url'])
                        st.link_button("⬇️ Download Video", final_data['video_url'])
                        
                        st.success("🎉 Your video is ready! Generate platform variants using the post-processing API.")
                
            except requests.exceptions.Timeout:
                st.error("❌ Request timeout. Please try again.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2: ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

with tab2:
    st.markdown("### 📊 Production Analytics")
    
    if st.button("🔄 Refresh Analytics", use_container_width=False):
        try:
            cost_resp = requests.get(f"{API_BASE}/api/cost-summary", timeout=10)
            cost_resp.raise_for_status()
            summary = cost_resp.json()
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Videos", summary.get("total_videos", 0))
            with col2:
                st.metric("Avg Cost/Video", f"${summary.get('avg_cost_per_video', 0):.4f}")
            with col3:
                st.metric("Hero Videos", summary.get("hero_videos", 0))
            with col4:
                st.metric("Catalog Videos", summary.get("catalog_videos", 0))
            
            st.divider()
            
            # Cost breakdown
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 💰 Cost Summary")
                total_cost = summary.get('total_cost_usd', 0)
                st.metric("Total Spend", f"${total_cost:.2f}")
                
                hero_videos = summary.get("hero_videos", 0)
                catalog_videos = summary.get("catalog_videos", 0)
                total_videos = hero_videos + catalog_videos
                
                if total_videos > 0:
                    hero_pct = (hero_videos / total_videos) * 100
                    catalog_pct = (catalog_videos / total_videos) * 100
                    
                    st.progress(hero_pct / 100, text=f"🌟 Hero: {hero_pct:.1f}%")
                    st.progress(catalog_pct / 100, text=f"📦 Catalog: {catalog_pct:.1f}%")
            
            with col_right:
                st.markdown("#### 🎯 Performance vs Target")
                target_cost = 0.16
                avg_cost = summary.get('avg_cost_per_video', 0)
                
                if avg_cost > 0:
                    savings = ((target_cost - avg_cost) / target_cost) * 100
                    
                    if savings > 0:
                        st.success(f"✅ **{savings:.1f}% under target**")
                        st.caption(f"Saving ${target_cost - avg_cost:.4f} per video")
                    else:
                        st.warning(f"⚠️ **{abs(savings):.1f}% over target**")
                    
                    st.caption(f"Target: ${target_cost}/video · Actual: ${avg_cost:.4f}/video")
                else:
                    st.info("Generate videos to see performance metrics")
        
        except Exception as e:
            st.error(f"Unable to load analytics: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption(f"🎬 AdCamp v1.1 · BytePlus ModelArk")

with col2:
    api_docs_url = f"{API_BASE}/docs"
    st.caption(f"📖 [API Docs]({api_docs_url})")

with col3:
    st.caption("Powered by Seed 1.8 & Seedance")
