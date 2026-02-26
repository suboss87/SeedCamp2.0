"""
Dashboard sections — rendering functions for sidebar, quick video,
campaign batch, and campaign history.
"""

import json

import requests
import streamlit as st
from PIL import Image

from config import (
    API_BASE,
    ACCENT,
    ACCENT_LIGHT,
    ACCENT_MUTED,
    TEXT_3,
    SIDEBAR_DIM,
    GREEN,
    GREEN_BG,
    RED,
    RED_BG,
    COST_TARGET_PER_VIDEO,
    cost_label,
    estimate_cost,
    status_badge,
    step_indicator,
    platform_pills_html,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA FETCHERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _fetch_analytics() -> dict:
    if st.session_state.get("_refresh_analytics"):
        st.session_state.pop("analytics_data", None)
        st.session_state["_refresh_analytics"] = False
    if "analytics_data" not in st.session_state:
        try:
            resp = requests.get(f"{API_BASE}/api/cost-summary", timeout=10)
            resp.raise_for_status()
            st.session_state["analytics_data"] = resp.json()
        except Exception:
            st.session_state["analytics_data"] = {}
    return st.session_state["analytics_data"]


def _fetch_safety_summary() -> dict:
    if st.session_state.get("_refresh_analytics"):
        st.session_state.pop("safety_data", None)
    if "safety_data" not in st.session_state:
        try:
            resp = requests.get(f"{API_BASE}/api/safety-summary", timeout=10)
            resp.raise_for_status()
            st.session_state["safety_data"] = resp.json()
        except Exception:
            st.session_state["safety_data"] = {}
    return st.session_state["safety_data"]


def _fetch_campaigns() -> list:
    if st.session_state.get("_refresh_campaigns"):
        st.session_state.pop("campaigns_list", None)
        st.session_state["_refresh_campaigns"] = False
    if "campaigns_list" not in st.session_state:
        try:
            resp = requests.get(f"{API_BASE}/api/campaigns", timeout=10)
            resp.raise_for_status()
            st.session_state["campaigns_list"] = resp.json()
        except Exception:
            st.session_state["campaigns_list"] = []
    return st.session_state["campaigns_list"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_sidebar_analytics():
    with st.sidebar:
        st.markdown(
            """
        <div class="ac-brand">
            <div class="ac-brand-logo">
                <div class="ac-brand-icon">A</div>
                <span class="ac-brand-name">AdCamp</span>
            </div>
            <p class="ac-brand-tag">AI Video Ad Generation</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        summary = _fetch_analytics()

        if not summary:
            st.markdown(
                """
            <div class="ac-empty-dark">
                <div class="ac-empty-icon">&#9671;</div>
                <div class="ac-empty-title">No analytics yet</div>
                <div class="ac-empty-desc">Generate your first video to see cost analytics and performance metrics here.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            if st.button("Refresh", use_container_width=True, key="sb_refresh"):
                st.session_state["_refresh_analytics"] = True
                st.rerun()
            return

        total_videos = summary.get("total_videos", 0)
        hero_videos = summary.get("hero_videos", 0)
        catalog_videos = summary.get("catalog_videos", 0)
        total_cost = summary.get("total_cost_usd", 0)
        avg_cost = summary.get("avg_cost_per_video", 0)

        st.markdown('<div class="ac-label">Overview</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
        <div class="ac-stat">
            <span class="ac-stat-label">Videos</span>
            <span class="ac-stat-val">{total_videos}</span>
        </div>
        <div class="ac-stat">
            <span class="ac-stat-label">Total Spend</span>
            <span class="ac-stat-val">${total_cost:.2f}</span>
        </div>
        <div class="ac-stat">
            <span class="ac-stat-label">Avg / Video</span>
            <span class="ac-stat-val accent">${avg_cost:.4f}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="ac-label">Tier Mix</div>', unsafe_allow_html=True)

        if total_videos > 0:
            hero_pct = (hero_videos / total_videos) * 100
            catalog_pct = (catalog_videos / total_videos) * 100
            st.markdown(
                f"""
            <div class="ac-tier">
                <span>Hero &middot; {hero_videos} ({hero_pct:.0f}%)</span>
                <div class="ac-tier-bar"><div class="ac-tier-fill" style="width:{hero_pct}%"></div></div>
            </div>
            <div class="ac-tier">
                <span>Catalog &middot; {catalog_videos} ({catalog_pct:.0f}%)</span>
                <div class="ac-tier-bar"><div class="ac-tier-fill" style="width:{catalog_pct}%"></div></div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("No videos generated yet")

        st.markdown('<div class="ac-label">Performance</div>', unsafe_allow_html=True)

        if avg_cost > 0:
            savings = ((COST_TARGET_PER_VIDEO - avg_cost) / COST_TARGET_PER_VIDEO) * 100
            if savings > 0:
                st.metric(
                    "Cost vs Target",
                    f"${avg_cost:.4f}/video",
                    delta=f"{savings:.1f}% under target",
                )
            else:
                st.metric(
                    "Cost vs Target",
                    f"${avg_cost:.4f}/video",
                    delta=f"{abs(savings):.1f}% over target",
                    delta_color="inverse",
                )
        else:
            st.caption("Generate videos to see cost metrics")

        # Safety evaluation metrics
        safety = _fetch_safety_summary()
        if safety and safety.get("total_checks", 0) > 0:
            st.markdown(
                '<div class="ac-label">Content Safety</div>', unsafe_allow_html=True
            )
            checks = safety.get("total_checks", 0)
            flagged = safety.get("total_flagged", 0)
            blocked = safety.get("total_blocked", 0)
            block_rate = safety.get("block_rate", 0) * 100

            st.markdown(
                f"""
            <div class="ac-stat">
                <span class="ac-stat-label">Safety Checks</span>
                <span class="ac-stat-val">{checks}</span>
            </div>
            <div class="ac-stat">
                <span class="ac-stat-label">Flagged</span>
                <span class="ac-stat-val">{flagged}</span>
            </div>
            <div class="ac-stat">
                <span class="ac-stat-label">Blocked</span>
                <span class="ac-stat-val">{blocked}</span>
            </div>
            <div class="ac-stat">
                <span class="ac-stat-label">Block Rate</span>
                <span class="ac-stat-val">{block_rate:.1f}%</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button(
            "Refresh Analytics", use_container_width=True, key="sb_refresh_analytics"
        ):
            st.session_state["_refresh_analytics"] = True
            st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SSE PIPELINE RUNNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _run_sse_generation(
    payload, progress_area, script_area, cost_area, video_area, variant_label=""
) -> dict:
    header = (
        f"Pipeline Progress — {variant_label}" if variant_label else "Pipeline Progress"
    )

    with progress_area:
        st.markdown(f"#### {header}")
        progress_bar = st.progress(0)
        step_placeholders = {i: st.empty() for i in range(1, 6)}

        try:
            response = requests.post(
                f"{API_BASE}/api/generate-stream",
                json=payload,
                stream=True,
                timeout=360,
            )
            final_data = {}
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                data = json.loads(line[6:])
                step = data.get("step")
                status = data.get("status")
                message = data.get("message", "")
                progress = data.get("progress", 0)
                progress_bar.progress(progress / 100)
                if step and step in step_placeholders:
                    css = status if status in ("running", "complete", "failed") else ""
                    icon = step_indicator(status)
                    step_placeholders[step].markdown(
                        f"""
                    <div class="ac-step {css}">
                        <span class="ac-step-num">Step {step}</span>
                        <span class="ac-step-msg">{message}</span>
                        <span class="ac-step-icon">{icon}</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                if "data" in data:
                    final_data.update(data["data"])
                if status == "complete" and step == 5:
                    break
                elif status in ("failed", "error", "timeout"):
                    with progress_area:
                        st.error(message)
                    return {}

            with script_area:
                if "script" in final_data:
                    s = final_data["script"]
                    label = (
                        f"View Generated Script — {variant_label}"
                        if variant_label
                        else "View Generated Script"
                    )
                    with st.expander(label, expanded=False):
                        st.markdown(f"**{s.get('ad_copy', 'N/A')}**")
                        st.caption(s.get("scene_description", ""))

            with cost_area:
                if "cost" in final_data:
                    cost = final_data["cost"]
                    cc1, cc2, cc3 = st.columns(3)
                    with cc1:
                        st.metric(
                            "Script Cost", f"${cost.get('script_cost_usd', 0):.4f}"
                        )
                    with cc2:
                        st.metric("Video Cost", f"${cost.get('video_cost_usd', 0):.4f}")
                    with cc3:
                        st.metric("Total Cost", f"${cost.get('total_cost_usd', 0):.4f}")

            with video_area:
                if "video_url" in final_data:
                    st.success(
                        "Video generated successfully!", icon=":material/check_circle:"
                    )
                    st.video(final_data["video_url"])
                    st.link_button(
                        "Download Video",
                        final_data["video_url"],
                        use_container_width=True,
                    )
            return final_data

        except requests.exceptions.Timeout:
            with progress_area:
                st.error("Request timed out. Please try again.")
            return {}
        except Exception as e:
            with progress_area:
                st.error(f"Error: {e}")
            return {}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# A/B COMPARISON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _render_ab_comparison(result_a: dict, result_b: dict, label_a: str, label_b: str):
    st.markdown("#### A/B Comparison")
    col_a, col_b = st.columns(2)
    for col, result, label in [(col_a, result_a, label_a), (col_b, result_b, label_b)]:
        with col:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                if not result:
                    st.warning("Generation failed")
                    continue
                if "video_url" in result:
                    st.video(result["video_url"])
                    st.link_button(
                        "Download", result["video_url"], use_container_width=True
                    )
                cost = result.get("cost", {})
                total = cost.get("total_cost_usd", 0)
                st.metric("Total Cost", f"${total:.4f}")
                script = result.get("script", {})
                ad_copy = script.get("ad_copy", "")
                if ad_copy:
                    st.caption(ad_copy[:120])

    cost_a = result_a.get("cost", {}).get("total_cost_usd", 0) if result_a else 0
    cost_b = result_b.get("cost", {}).get("total_cost_usd", 0) if result_b else 0

    if cost_a > 0 and cost_b > 0:
        delta = cost_b - cost_a
        pct = (abs(delta) / max(cost_a, cost_b)) * 100
        if delta > 0:
            winner = label_a
            summary = f"{label_a} is **${abs(delta):.4f} cheaper** ({pct:.0f}% less)"
        elif delta < 0:
            winner = label_b
            summary = f"{label_b} is **${abs(delta):.4f} cheaper** ({pct:.0f}% less)"
        else:
            winner = "Tie"
            summary = "Both variants cost the same"

        with st.container(border=True):
            sc1, sc2 = st.columns([1, 2])
            with sc1:
                st.metric("Cost Winner", winner)
            with sc2:
                st.markdown(summary)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUICK VIDEO TAB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_quick_video():
    st.caption("Generate a single video ad for testing the pipeline")

    st.markdown("#### Campaign Brief")
    brief = st.text_area(
        "Campaign Brief",
        placeholder="Describe your product, target audience, mood, and key message...",
        height=120,
        label_visibility="collapsed",
    )

    st.markdown("#### Configuration")

    with st.container(border=True):
        cfg1, cfg2, cfg3, cfg4 = st.columns(4)
        with cfg1:
            sku_tier = st.selectbox(
                "SKU Tier",
                ["catalog", "hero"],
                index=0,
                format_func=lambda x: "Hero" if x == "hero" else "Catalog",
            )
        with cfg2:
            duration = st.selectbox(
                "Duration",
                [2, 4, 6, 8, 10, 12],
                index=3,
                format_func=lambda x: f"{x}s",
            )
        with cfg3:
            resolution = st.selectbox("Resolution", ["480p", "720p", "1080p"], index=1)
        with cfg4:
            sku_id = st.text_input("SKU ID", value="SKU-001")

        cfg5, cfg6 = st.columns(2)
        with cfg5:
            platforms = st.multiselect(
                "Platforms",
                ["tiktok", "instagram", "youtube"],
                default=["tiktok"],
                format_func=str.capitalize,
            )
            if platforms:
                st.markdown(
                    f'<div style="display:flex;gap:0.35rem;flex-wrap:wrap;margin-top:-0.3rem;">'
                    f"{platform_pills_html(platforms)}</div>",
                    unsafe_allow_html=True,
                )
        with cfg6:
            est_label = cost_label(sku_tier, duration, resolution)
            st.markdown(
                f'<div style="display:flex;justify-content:flex-end;padding-top:1.6rem;">'
                f'<div class="ac-pill">Est. {est_label}</div></div>',
                unsafe_allow_html=True,
            )

    with st.expander("Product Image (optional)"):
        uploaded_file = st.file_uploader(
            "Upload product image",
            type=["jpg", "jpeg", "png"],
            help="Min height: 300px. Improves video quality.",
            label_visibility="collapsed",
        )
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption=None, use_container_width=True)
            width, height = image.size
            if height < 300:
                st.warning(f"Image height ({height}px) is below the 300px minimum")
            else:
                st.caption(f"{width} x {height}px")

    _AB_DIMENSIONS = {
        "Model Tier": "sku_tier",
        "Duration": "duration",
        "Resolution": "resolution",
        "Platform": "platforms",
    }
    _AB_OPTIONS = {
        "sku_tier": ["catalog", "hero"],
        "duration": [2, 4, 6, 8, 10, 12],
        "resolution": ["480p", "720p", "1080p"],
        "platforms": ["tiktok", "instagram", "youtube"],
    }
    _AB_FORMAT = {
        "sku_tier": lambda x: "Hero" if x == "hero" else "Catalog",
        "duration": lambda x: f"{x}s",
        "resolution": str,
        "platforms": str.capitalize,
    }

    ab_enabled = st.checkbox(
        "A/B Comparison",
        value=False,
        help="Generate two variants to compare side-by-side",
    )
    ab_field = None
    ab_variant_b = None

    if ab_enabled:
        with st.container(border=True):
            ab1, ab2 = st.columns(2)
            with ab1:
                dimension_label = st.selectbox(
                    "Compare by",
                    list(_AB_DIMENSIONS.keys()),
                )
                ab_field = _AB_DIMENSIONS[dimension_label]

            current_values = {
                "sku_tier": sku_tier,
                "duration": duration,
                "resolution": resolution,
                "platforms": platforms,
            }
            current_val = current_values[ab_field]
            all_options = _AB_OPTIONS[ab_field]
            fmt = _AB_FORMAT[ab_field]

            if ab_field == "platforms":
                b_options = [p for p in all_options if p not in current_val]
            else:
                b_options = [v for v in all_options if v != current_val]

            with ab2:
                if b_options:
                    ab_variant_b = st.selectbox(
                        "Variant B value",
                        b_options,
                        format_func=fmt,
                    )
                else:
                    st.warning("No alternative values available")
                    ab_enabled = False

            if ab_enabled and ab_field == "sku_tier":
                cost_a = cost_label(sku_tier, duration, resolution)
                cost_b = cost_label(ab_variant_b, duration, resolution)
                st.caption(f"A: **{cost_a}** vs B: **{cost_b}**")
            elif ab_enabled:
                fmt_a = (
                    fmt(current_val)
                    if ab_field != "platforms"
                    else ", ".join(current_val)
                )
                fmt_b = fmt(ab_variant_b)
                st.caption(
                    f"Two videos generated sequentially. "
                    f"A: **{fmt_a}** | B: **{fmt_b}**"
                )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    btn_label = "Generate A/B Comparison" if ab_enabled else "Generate Video"
    generate_btn = st.button(
        btn_label,
        type="primary",
        use_container_width=True,
        disabled=not brief,
    )

    if not brief and generate_btn:
        st.error("Please enter a campaign brief to continue.")

    if generate_btn and brief:
        image_url = None
        if uploaded_file:
            with st.spinner("Uploading image..."):
                try:
                    uploaded_file.seek(0)
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }
                    upload_resp = requests.post(
                        f"{API_BASE}/api/upload-image",
                        files=files,
                        timeout=30,
                    )
                    upload_resp.raise_for_status()
                    image_url = upload_resp.json().get("url")
                except Exception as e:
                    st.warning(
                        f"Image upload failed: {e}. " "Continuing without image."
                    )

        payload_a = {
            "brief": brief,
            "product_image_url": image_url,
            "sku_tier": sku_tier,
            "sku_id": sku_id,
            "platforms": platforms,
            "duration": duration,
            "resolution": resolution,
        }

        if not ab_enabled:
            progress_area = st.container()
            script_area = st.container()
            cost_area = st.container()
            video_area = st.container()
            _run_sse_generation(
                payload_a, progress_area, script_area, cost_area, video_area
            )
        else:
            fmt = _AB_FORMAT[ab_field]
            current_val = {
                "sku_tier": sku_tier,
                "duration": duration,
                "resolution": resolution,
                "platforms": platforms,
            }[ab_field]

            if ab_field == "platforms":
                label_a = (
                    f"Variant A: " f"{', '.join(p.capitalize() for p in platforms)}"
                )
                label_b = f"Variant B: {ab_variant_b.capitalize()}"
            else:
                label_a = f"Variant A: {fmt(current_val)}"
                label_b = f"Variant B: {fmt(ab_variant_b)}"

            payload_b = {**payload_a}
            if ab_field == "platforms":
                payload_b["platforms"] = [ab_variant_b]
            else:
                payload_b[ab_field] = ab_variant_b

            pa_progress = st.container()
            pa_script = st.container()
            pa_cost = st.container()
            pa_video = st.container()
            result_a = _run_sse_generation(
                payload_a, pa_progress, pa_script, pa_cost, pa_video, label_a
            )

            pb_progress = st.container()
            pb_script = st.container()
            pb_cost = st.container()
            pb_video = st.container()
            result_b = _run_sse_generation(
                payload_b, pb_progress, pb_script, pb_cost, pb_video, label_b
            )

            if not result_a and not result_b:
                st.error("Both variants failed to generate.")
            elif not result_a or not result_b:
                failed = label_a if not result_a else label_b
                st.warning(f"{failed} failed. Showing available result only.")
                _render_ab_comparison(result_a, result_b, label_a, label_b)
            else:
                _render_ab_comparison(result_a, result_b, label_a, label_b)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAMPAIGN BATCH TAB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_campaign_batch():
    st.caption("Create campaigns, upload products, and generate videos at scale")

    campaigns = _fetch_campaigns()
    active_id = st.session_state.get("active_campaign_id")

    st.markdown("#### Campaign")

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.markdown("**Create New**")
            name = st.text_input(
                "Name", placeholder="e.g. Summer 2025 Collection", key="cb_name"
            )
            theme = st.text_area(
                "Theme",
                placeholder="Describe the overall mood, aesthetic, and message...",
                height=80,
                key="cb_theme",
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                platforms = st.multiselect(
                    "Platforms",
                    ["tiktok", "instagram", "youtube"],
                    default=["tiktok"],
                    format_func=str.capitalize,
                    key="cb_platforms",
                )
                if platforms:
                    st.markdown(
                        f'<div style="display:flex;gap:0.35rem;flex-wrap:wrap;margin-top:-0.3rem;">'
                        f"{platform_pills_html(platforms)}</div>",
                        unsafe_allow_html=True,
                    )
            with c2:
                duration = st.selectbox(
                    "Duration",
                    [2, 4, 6, 8, 10, 12],
                    index=3,
                    format_func=lambda x: f"{x}s",
                    key="cb_duration",
                )
            with c3:
                resolution = st.selectbox(
                    "Resolution",
                    ["480p", "720p", "1080p"],
                    index=1,
                    key="cb_resolution",
                )

            if st.button(
                "Create Campaign",
                type="primary",
                disabled=not (name and theme),
                key="cb_create",
                use_container_width=True,
            ):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/campaigns",
                        json={
                            "name": name,
                            "theme": theme,
                            "platforms": platforms,
                            "duration": duration,
                            "resolution": resolution,
                        },
                        timeout=10,
                    )
                    resp.raise_for_status()
                    new_id = resp.json()["id"]
                    st.session_state["active_campaign_id"] = new_id
                    st.session_state["_refresh_campaigns"] = True
                    st.toast("Campaign created!", icon=":material/check_circle:")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

    with right:
        with st.container(border=True):
            st.markdown("**Or Load Existing**")
            if campaigns:
                campaign_options = {c["id"]: c["name"] for c in campaigns}
                ids = list(campaign_options.keys())
                default_idx = ids.index(active_id) if active_id in ids else 0
                selected_id = st.selectbox(
                    "Select Campaign",
                    ids,
                    index=default_idx,
                    format_func=lambda x: campaign_options.get(x, x),
                    key="cb_select",
                )
                if st.button("Load Campaign", use_container_width=True, key="cb_load"):
                    st.session_state["active_campaign_id"] = selected_id
                    st.rerun()
            else:
                st.markdown(
                    """
                <div class="ac-empty">
                    <div class="ac-empty-icon">&#128203;</div>
                    <div class="ac-empty-title">No campaigns yet</div>
                    <div class="ac-empty-desc">Create your first campaign to get started.</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    if not active_id:
        return

    active_campaign = next((c for c in campaigns if c.get("id") == active_id), None)
    if active_campaign:
        st.info(
            f"Active: **{active_campaign['name']}** "
            f"{status_badge(active_campaign.get('status', 'draft'))}"
        )
    else:
        st.info(f"Active campaign: `{active_id}`")

    st.markdown("#### Products")
    st.caption(
        "CSV columns: `sku_id`, `product_name`, `description` (required) "
        "`image_url`, `sku_tier`, `category` (optional)"
    )

    uploaded_csv = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        label_visibility="collapsed",
        key="cb_csv",
    )

    if uploaded_csv and st.button(
        "Upload Products", type="primary", key="cb_upload", use_container_width=True
    ):
        with st.spinner("Parsing..."):
            try:
                files = {
                    "file": (uploaded_csv.name, uploaded_csv.getvalue(), "text/csv")
                }
                resp = requests.post(
                    f"{API_BASE}/api/campaigns/{active_id}/products",
                    files=files,
                    timeout=30,
                )
                resp.raise_for_status()
                r = resp.json()
                st.toast(
                    f"{r['products_created']} products uploaded",
                    icon=":material/check_circle:",
                )
                if r.get("errors"):
                    with st.expander(f"{r['products_skipped']} rows skipped"):
                        for err in r["errors"]:
                            st.caption(err)
            except Exception as e:
                st.error(f"Upload failed: {e}")

    try:
        products = requests.get(
            f"{API_BASE}/api/campaigns/{active_id}/products", timeout=10
        ).json()
    except Exception:
        products = []

    if products:
        st.caption(f"**{len(products)} products** loaded")
        with st.container(border=True):
            for p in products[:15]:
                tier = "Hero" if p.get("sku_tier") == "hero" else "Catalog"
                st.markdown(f"`{p['sku_id']}` {p['product_name']} — {tier}")
            if len(products) > 15:
                st.caption(f"+ {len(products) - 15} more")

    if products:
        st.markdown("#### Generate Videos")

        pending_count = sum(1 for p in products if p.get("status") == "pending")
        if pending_count == 0:
            st.success("All products have been processed. " "See results below.")
        else:
            gc1, gc2 = st.columns([2, 1])
            with gc1:
                concurrency = st.slider("Parallel jobs", 1, 10, 3, key="cb_concurrency")
            with gc2:
                st.markdown(
                    f'<div class="ac-pill" style="margin-top:1.5rem">'
                    f"{pending_count} products ready</div>",
                    unsafe_allow_html=True,
                )

            if st.button(
                "Start Generation",
                type="primary",
                use_container_width=True,
                key="cb_generate",
            ):
                try:
                    requests.post(
                        f"{API_BASE}/api/campaigns/{active_id}/generate",
                        json={"concurrency": concurrency},
                        timeout=10,
                    ).raise_for_status()
                    st.session_state["polling_campaign_id"] = active_id
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

    if st.session_state.get("polling_campaign_id") == active_id:
        _poll_batch_progress(active_id)

    _render_campaign_results(active_id)


# ── Campaign results ─────────────────────────────────────────────────────────


def _render_campaign_results(campaign_id: str):
    try:
        results_resp = requests.get(
            f"{API_BASE}/api/campaigns/{campaign_id}/results", timeout=10
        )
        results_resp.raise_for_status()
        results = results_resp.json()
    except Exception:
        return

    if not results:
        return

    completed = [r for r in results if r.get("status") == "completed"]
    failed = [r for r in results if r.get("status") == "failed"]

    if completed:
        st.markdown(f"#### Completed Videos ({len(completed)})")
        for i in range(0, len(completed), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(completed):
                    break
                result = completed[idx]
                with col:
                    with st.container(border=True):
                        video_url = result.get("video_url")
                        if video_url:
                            st.video(video_url)

                        product_id = result.get("product_id", "N/A")
                        st.caption(f"SKU: `{product_id}`")

                        script = result.get("script", {})
                        if script:
                            ad_copy = script.get("ad_copy", "")
                            if ad_copy:
                                st.markdown(f"**{ad_copy}**")
                            scene = script.get("scene_description", "")
                            if scene:
                                st.caption(scene[:120])

                        cost = result.get("cost", {})
                        model = result.get("model_used", "N/A")
                        cost_val = cost.get("total_cost_usd", 0) if cost else 0
                        st.caption(f"{model} — ${cost_val:.4f}")

                        if video_url:
                            st.link_button(
                                "Download", video_url, use_container_width=True
                            )

    if failed:
        with st.expander(f"Failed ({len(failed)})"):
            for r in failed:
                pid = r.get("product_id", "N/A")
                err = r.get("error", "Unknown error")
                st.caption(f"`{pid}`: {err}")


# ── Batch progress polling ───────────────────────────────────────────────────


@st.fragment(run_every=3)
def _poll_batch_progress(campaign_id: str):
    st.markdown("#### Generation Progress")

    try:
        p = requests.get(
            f"{API_BASE}/api/campaigns/{campaign_id}/progress", timeout=10
        ).json()
    except Exception:
        st.caption("Waiting for progress data...")
        return

    total = p.get("total_products", 1)
    done = p.get("completed_videos", 0) + p.get("failed_videos", 0)
    pct = p.get("progress_pct", 0)
    status = p.get("status", "generating")

    st.progress(pct / 100, text=f"{done}/{total} processed")

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("Completed", p.get("completed_videos", 0))
    with mc2:
        st.metric("Failed", p.get("failed_videos", 0))
    with mc3:
        st.metric("Cost", f"${p.get('total_cost_usd', 0):.4f}")

    if status in ("completed", "partial", "failed"):
        if status == "completed":
            st.toast("All videos generated!", icon=":material/check_circle:")
            st.success("All videos generated successfully")
        elif status == "partial":
            st.toast(
                "Generation completed with some failures", icon=":material/warning:"
            )
            st.warning(
                f"{p.get('completed_videos', 0)} succeeded, "
                f"{p.get('failed_videos', 0)} failed"
            )
        else:
            st.toast("Batch generation failed", icon=":material/error:")
            st.error("Batch generation failed")
        del st.session_state["polling_campaign_id"]


# ── Delete campaign dialog ───────────────────────────────────────────────────


@st.dialog("Delete Campaign")
def _confirm_delete(campaign_id: str, campaign_name: str):
    st.write(f"Are you sure you want to delete **{campaign_name}**?")
    st.caption("This action cannot be undone.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", use_container_width=True, key="del_cancel"):
            st.rerun()
    with c2:
        if st.button(
            "Delete", type="primary", use_container_width=True, key="del_confirm"
        ):
            try:
                requests.delete(
                    f"{API_BASE}/api/campaigns/{campaign_id}", timeout=10
                ).raise_for_status()
                st.session_state["_refresh_campaigns"] = True
                st.session_state["_refresh_analytics"] = True
                if st.session_state.get("active_campaign_id") == campaign_id:
                    del st.session_state["active_campaign_id"]
                st.toast("Campaign deleted", icon=":material/check_circle:")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAMPAIGN HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_campaign_history():
    campaigns = _fetch_campaigns()

    with st.expander(f"Campaign History ({len(campaigns)})", expanded=False):
        if not campaigns:
            st.markdown(
                """
            <div class="ac-empty">
                <div class="ac-empty-icon">&#128203;</div>
                <div class="ac-empty-title">No campaigns yet</div>
                <div class="ac-empty-desc">Create a campaign in the Campaign Batch tab to get started.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            return

        for c in campaigns:
            status = c.get("status", "draft")
            done = c.get("completed_videos", 0)
            total_p = c.get("total_products", 0)
            cost = c.get("total_cost_usd", 0)
            created = c.get("created_at", "")[:10]
            campaign_platforms = c.get("platforms", [])

            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.markdown(f"**{c['name']}** {status_badge(status)}")
                    if campaign_platforms:
                        st.markdown(
                            f'<div style="display:flex;gap:0.3rem;flex-wrap:wrap;margin:0.15rem 0 0.2rem;">'
                            f"{platform_pills_html(campaign_platforms)}</div>",
                            unsafe_allow_html=True,
                        )
                    meta_parts = []
                    if c.get("duration"):
                        meta_parts.append(f'{c["duration"]}s')
                    if created:
                        meta_parts.append(created)
                    if meta_parts:
                        st.caption(" · ".join(meta_parts))

                with right:
                    st.caption(f"{done}/{total_p} videos · ${cost:.2f}")

                ac1, ac2 = st.columns(2)
                with ac1:
                    if done > 0:
                        if st.button(
                            "View Results",
                            key=f"hist_view_{c['id']}",
                            use_container_width=True,
                        ):
                            st.session_state["active_campaign_id"] = c["id"]
                            st.rerun()
                with ac2:
                    if st.button(
                        "Delete", key=f"hist_del_{c['id']}", use_container_width=True
                    ):
                        _confirm_delete(c["id"], c["name"])
