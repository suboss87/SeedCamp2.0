"""
AdCamp — AI Video Ad Generation Dashboard
Single-page layout: sidebar analytics + two tabs + campaign history
"""
import streamlit as st

from config import (
    ACCENT, ACCENT_LIGHT,
    BORDER,
    SUCCESS, SUCCESS_LIGHT, ERROR, ERROR_LIGHT,
    TEXT_SECONDARY, TEXT_TERTIARY,
    SHADOW_SM, SHADOW_MD,
    API_BASE,
)
from sections import (
    render_sidebar_analytics,
    render_quick_video,
    render_campaign_batch,
    render_campaign_history,
)

# =============================================================================
#  PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="AdCamp",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
#  GLOBAL CSS — Minimal overrides (theme handled by .streamlit/config.toml)
# =============================================================================

st.markdown(f"""
<style>
    /* ─── Inter font ─── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    h1, h2, h3, h4 {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 700;
        letter-spacing: -0.025em;
    }}
    .block-container {{
        padding: 2.5rem 2rem 2rem 2rem;
        max-width: 980px;
    }}

    /* ─── Cards (shadow-on-hover) ─── */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border: none !important;
        border-radius: 12px !important;
        box-shadow: {SHADOW_SM} !important;
        transition: box-shadow 0.2s ease !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        box-shadow: {SHADOW_MD} !important;
    }}

    /* ─── Pipeline step component ─── */
    .ac-step {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        font-size: 0.875rem;
        color: {TEXT_SECONDARY};
        border-radius: 10px;
        margin-bottom: 4px;
        transition: all 0.2s ease;
    }}
    .ac-step-num {{
        font-size: 0.7rem;
        font-weight: 700;
        color: {TEXT_TERTIARY};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        min-width: 3.5rem;
    }}
    .ac-step-msg {{ flex: 1; font-weight: 500; }}
    .ac-step-icon {{ font-size: 1rem; min-width: 1.5rem; text-align: center; }}
    .ac-step.running {{ background: {ACCENT_LIGHT}; }}
    .ac-step.running .ac-step-icon {{ color: {ACCENT}; font-weight: 700; }}
    .ac-step.complete {{ background: {SUCCESS_LIGHT}; }}
    .ac-step.complete .ac-step-icon {{ color: {SUCCESS}; }}
    .ac-step.failed {{ background: {ERROR_LIGHT}; }}
    .ac-step.failed .ac-step-icon {{ color: {ERROR}; }}

    /* ─── Metric label override ─── */
    [data-testid="stMetricLabel"] {{
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
    }}

    /* ─── Footer ─── */
    .ac-footer {{
        text-align: center;
        color: {TEXT_TERTIARY};
        font-size: 0.75rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid {BORDER};
        margin-top: 3rem;
    }}
    .ac-footer a {{ color: {ACCENT}; text-decoration: none; font-weight: 500; }}

    /* ─── Hide Streamlit defaults ─── */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
#  SESSION STATE DEFAULTS
# =============================================================================

_defaults = {
    "active_campaign_id": None,
    "polling_campaign_id": None,
    "_refresh_campaigns": False,
    "_refresh_analytics": False,
}
for key, value in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =============================================================================
#  SIDEBAR: Analytics
# =============================================================================

render_sidebar_analytics()

# =============================================================================
#  MAIN: Tabs
# =============================================================================

tab_video, tab_campaign = st.tabs(["Quick Video", "Campaign Batch"])

with tab_video:
    render_quick_video()

with tab_campaign:
    render_campaign_batch()

# =============================================================================
#  CAMPAIGN HISTORY (below tabs)
# =============================================================================

st.divider()
render_campaign_history()

# =============================================================================
#  FOOTER
# =============================================================================

api_docs_url = f"{API_BASE}/docs"
st.markdown(f"""
<div class="ac-footer">
    AdCamp v2.0 &middot; Powered by BytePlus ModelArk &middot;
    <a href="{api_docs_url}" target="_blank">API Docs</a>
</div>
""", unsafe_allow_html=True)
