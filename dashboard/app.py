"""
AdCamp — AI Video Ad Generation Dashboard
"""

import streamlit as st

from config import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_LIGHT,
    ACCENT_MUTED,
    ACCENT_GRAD,
    SIDEBAR_BG,
    SIDEBAR_CARD,
    SIDEBAR_BORDER,
    SIDEBAR_TEXT,
    SIDEBAR_DIM,
    BG_PAGE,
    BG_CARD,
    BG_SURFACE,
    BG_HOVER,
    BORDER,
    BORDER_LIGHT,
    TEXT,
    TEXT_2,
    TEXT_3,
    GREEN,
    GREEN_BG,
    RED,
    RED_BG,
    AMBER,
    AMBER_BG,
    SHADOW_SM,
    SHADOW_MD,
    SHADOW_LG,
    RADIUS,
    RADIUS_SM,
    RADIUS_LG,
    API_BASE,
)
from sections import (
    render_sidebar_analytics,
    render_quick_video,
    render_campaign_batch,
    render_campaign_history,
)

st.set_page_config(
    page_title="AdCamp",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL STYLESHEET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset & Base ────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}}
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
[data-testid="stMain"] > div,
[data-testid="stMainBlockContainer"],
[data-testid="stBottom"],
.main,
.main .block-container {{
    background-color: {BG_PAGE} !important;
    color: {TEXT} !important;
}}
.stApp {{
    background-color: {BG_PAGE} !important;
}}
.block-container {{
    padding: 2.25rem 3rem 3rem 3rem !important;
    max-width: 1100px !important;
}}

/* ── Hide Streamlit chrome ───────────────────────────── */
#MainMenu, footer, .stDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"] {{ display: none !important; }}
header[data-testid="stHeader"] {{
    background: transparent !important;
    backdrop-filter: none !important;
    height: 2.5rem !important;
    overflow: visible !important;
}}

/* ── Typography ──────────────────────────────────────── */
[data-testid="stMain"] h1 {{ font-weight: 800 !important; letter-spacing: -0.04em !important; font-size: 1.65rem !important; line-height: 1.15 !important; color: {TEXT} !important; }}
[data-testid="stMain"] h2 {{ font-weight: 700 !important; letter-spacing: -0.03em !important; font-size: 1.2rem !important; color: {TEXT} !important; margin-top: 0.15rem !important; }}
[data-testid="stMain"] h3 {{ font-weight: 700 !important; letter-spacing: -0.025em !important; font-size: 1.05rem !important; color: {TEXT} !important; }}
[data-testid="stMain"] h4 {{ font-weight: 600 !important; letter-spacing: -0.02em !important; font-size: 0.95rem !important; color: {TEXT} !important; }}
p, span, div {{ font-family: 'Inter', sans-serif !important; }}
[data-testid="stMain"] p,
[data-testid="stMain"] span,
[data-testid="stMain"] label,
[data-testid="stMain"] [data-testid="stCaptionContainer"] {{
    color: {TEXT_2} !important;
}}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p {{
    color: {TEXT} !important;
}}

/* ── SIDEBAR — Dark professional ─────────────────────── */
section[data-testid="stSidebar"] {{
    background: {SIDEBAR_BG} !important;
    border-right: none !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.15) !important;
}}
section[data-testid="stSidebar"] .block-container {{
    padding: 1.25rem 1.25rem !important;
}}
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}}
/* ── Sidebar toggle arrows — ALWAYS visible ────────── */
/* Collapse arrow inside the open sidebar */
section[data-testid="stSidebar"] button[kind="header"],
section[data-testid="stSidebar"] [data-testid="baseButton-header"] {{
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    width: 32px !important;
    height: 32px !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    position: relative !important;
    z-index: 100 !important;
}}
section[data-testid="stSidebar"] button[kind="header"]:hover,
section[data-testid="stSidebar"] [data-testid="baseButton-header"]:hover {{
    background: rgba(255,255,255,0.2) !important;
}}
section[data-testid="stSidebar"] button[kind="header"] svg,
section[data-testid="stSidebar"] [data-testid="baseButton-header"] svg {{
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    width: 20px !important;
    height: 20px !important;
}}
/* Expand arrow when sidebar is collapsed — FORCE always visible */
[data-testid="collapsedControl"],
[data-testid="collapsedControl"] * {{
    opacity: 1 !important;
    visibility: visible !important;
    pointer-events: auto !important;
}}
[data-testid="collapsedControl"] {{
    display: block !important;
    z-index: 999999 !important;
    transition: none !important;
}}
[data-testid="collapsedControl"] button,
[data-testid="collapsedControl"] [data-testid="baseButton-header"] {{
    background: {BG_CARD} !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    width: 36px !important;
    height: 36px !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: background 0.15s ease !important;
}}
[data-testid="collapsedControl"] button:hover,
[data-testid="collapsedControl"] [data-testid="baseButton-header"]:hover {{
    background: #F1F5F9 !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.15) !important;
}}
[data-testid="collapsedControl"] svg {{
    fill: #1E293B !important;
    color: #1E293B !important;
    width: 20px !important;
    height: 20px !important;
    opacity: 1 !important;
    visibility: visible !important;
}}
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border: none !important;
    box-shadow: none !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
    color: {SIDEBAR_TEXT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {{
    color: {SIDEBAR_DIM} !important;
}}
section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{
    color: #F1F5F9 !important;
}}
section[data-testid="stSidebar"] .stProgress > div > div {{
    background: rgba(255,255,255,0.08) !important;
}}
section[data-testid="stSidebar"] .stProgress > div > div > div {{
    background: {ACCENT_GRAD} !important;
}}
section[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: {SIDEBAR_TEXT} !important;
    border-radius: {RADIUS_SM} !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    transition: all 0.2s ease !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.18) !important;
    color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] [data-testid="stMetricDelta"] {{
    color: {GREEN} !important;
}}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
section[data-testid="stSidebar"] [data-testid="stTextInput"] input,
section[data-testid="stSidebar"] [data-testid="stTextArea"] textarea {{
    background: {SIDEBAR_CARD} !important;
    border-color: {SIDEBAR_BORDER} !important;
    color: {SIDEBAR_TEXT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stExpander"] {{
    background: {SIDEBAR_CARD} !important;
    border-color: {SIDEBAR_BORDER} !important;
}}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
    color: {SIDEBAR_TEXT} !important;
}}

/* ── Main content: strip all wrapper borders by default ─ */
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMainBlockContainer"] [data-testid="stTabs"] > [data-testid="stVerticalBlockBorderWrapper"] {{
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}}

/* ── Cards (containers with border=True) ─────────────── */
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlockBorderWrapper"][style*="border"] {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS} !important;
    box-shadow: {SHADOW_SM} !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    overflow: hidden !important;
    background: {BG_CARD} !important;
}}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlockBorderWrapper"][style*="border"]:hover {{
    box-shadow: {SHADOW_MD} !important;
}}

/* ── Tabs (segmented pill style) ─────────────────────── */
[data-testid="stTabs"] {{
    background-color: {BG_PAGE} !important;
}}
[data-testid="stTabContent"] > div {{
    background-color: {BG_PAGE} !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    gap: 4px !important;
    border-bottom: none !important;
    padding: 4px !important;
    background-color: {BG_SURFACE} !important;
    border-radius: 10px !important;
    display: inline-flex !important;
    width: auto !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    display: none !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: -0.01em !important;
    padding: 0.5rem 1.25rem !important;
    border-radius: 7px !important;
    border-bottom: none !important;
    color: {TEXT_3} !important;
    transition: all 0.15s ease !important;
    margin-bottom: 0 !important;
    background: transparent !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {{
    color: {TEXT_2} !important;
    background: rgba(0,0,0,0.03) !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {TEXT} !important;
    font-weight: 600 !important;
    border-bottom: none !important;
    background: {BG_CARD} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04) !important;
}}
[data-testid="stTabContent"] {{
    padding-top: 1.5rem !important;
}}

/* ── Force all main-area widget backgrounds to white ──── */
[data-testid="stMain"] [data-baseweb="select"],
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="input"] > div,
[data-testid="stMain"] [data-baseweb="textarea"],
[data-testid="stMain"] [data-baseweb="popover"] > div,
[data-testid="stMain"] [data-baseweb="menu"],
[data-testid="stMain"] ul[role="listbox"] {{
    background-color: {BG_CARD} !important;
    color: {TEXT} !important;
}}
[data-testid="stMain"] [data-baseweb="select"] [data-baseweb="tag"],
[data-testid="stMain"] [data-baseweb="tag"] {{
    background-color: {ACCENT} !important;
    color: #FFFFFF !important;
}}
[data-testid="stMain"] [data-baseweb="tag"] span,
[data-testid="stMain"] [data-baseweb="tag"] svg,
[data-testid="stMain"] [data-baseweb="tag"] div {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}
[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
    background-color: {ACCENT} !important;
    color: #FFFFFF !important;
}}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}

/* ── Inputs ──────────────────────────────────────────── */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_SM} !important;
    padding: 0.7rem 0.9rem !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    background-color: {BG_CARD} !important;
    color: {TEXT} !important;
    line-height: 1.55 !important;
}}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT_LIGHT} !important;
    outline: none !important;
}}
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label {{
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: {TEXT_2} !important;
}}

/* ── Selects & multiselects ──────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_SM} !important;
    font-size: 0.85rem !important;
    transition: border-color 0.15s ease !important;
    background-color: {BG_CARD} !important;
    color: {TEXT} !important;
}}
[data-testid="stSelectbox"] > div > div:hover,
[data-testid="stMultiSelect"] > div > div:hover {{
    border-color: {TEXT_3} !important;
}}
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: {TEXT_2} !important;
}}
[data-testid="stSelectbox"] svg,
[data-testid="stMultiSelect"] svg {{
    fill: {TEXT_2} !important;
}}

/* ── Dropdown menus (rendered at body level) ─────────── */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="popover"] > div,
ul[role="listbox"],
ul[role="listbox"] li,
[data-baseweb="menu"] li,
[data-baseweb="menu"] ul {{
    background-color: {BG_CARD} !important;
    color: {TEXT} !important;
}}
ul[role="listbox"] li:hover,
[data-baseweb="menu"] li:hover {{
    background-color: {BG_SURFACE} !important;
}}
ul[role="listbox"] [aria-selected="true"],
[data-baseweb="menu"] [aria-selected="true"] {{
    background-color: {ACCENT_LIGHT} !important;
    color: {ACCENT} !important;
}}

/* ── Checkbox / toggle ───────────────────────────────── */
[data-testid="stMain"] [data-testid="stCheckbox"] label p,
[data-testid="stMain"] [data-testid="stCheckbox"] label span {{
    color: {TEXT} !important;
}}
[data-testid="stMain"] [data-testid="stCheckbox"] [data-testid="stWidgetLabel"] p {{
    font-weight: 500 !important;
    font-size: 0.88rem !important;
}}
[data-testid="stMain"] [data-testid="stCheckbox"] span[data-baseweb="checkbox"] {{
    border-color: #94A3B8 !important;
    border-width: 2px !important;
    border-radius: 4px !important;
    width: 20px !important;
    height: 20px !important;
}}
[data-testid="stMain"] [data-testid="stCheckbox"] input:checked + span[data-baseweb="checkbox"] {{
    background-color: {ACCENT} !important;
    border-color: {ACCENT} !important;
}}

/* ── Slider ──────────────────────────────────────────── */
[data-testid="stMain"] [data-baseweb="slider"] [data-testid="stThumbValue"] {{
    color: {TEXT} !important;
    background-color: {BG_CARD} !important;
}}

/* ── Number input ────────────────────────────────────── */
[data-testid="stMain"] [data-baseweb="input"] {{
    background-color: {BG_CARD} !important;
    color: {TEXT} !important;
}}

/* ── Primary button ──────────────────────────────────── */
.stButton > button[kind="primary"] {{
    background: {ACCENT} !important;
    color: white !important;
    border: none !important;
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 1px 2px rgba(99, 102, 241, 0.25) !important;
    transition: all 0.15s ease !important;
    letter-spacing: -0.01em !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: {ACCENT_HOVER} !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"]:active {{
    transform: translateY(0) !important;
}}

/* ── Secondary button ────────────────────────────────── */
.stButton > button[kind="secondary"],
.stButton > button:not([kind]) {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
    color: {TEXT_2} !important;
    background: {BG_CARD} !important;
    transition: all 0.15s ease !important;
    padding: 0.55rem 1.25rem !important;
}}
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind]):hover {{
    border-color: {TEXT_3} !important;
    color: {TEXT} !important;
    background: {BG_SURFACE} !important;
}}

/* ── Link buttons ────────────────────────────────────── */
.stLinkButton > a {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
    transition: all 0.15s ease !important;
}}
.stLinkButton > a:hover {{
    border-color: {TEXT_3} !important;
    color: {TEXT} !important;
}}

/* ── Metrics ─────────────────────────────────────────── */
[data-testid="stMetricLabel"] {{
    font-family: 'Inter', sans-serif !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-size: 0.67rem !important;
    font-weight: 600 !important;
    color: {TEXT_3} !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    font-size: 1.35rem !important;
}}
[data-testid="stMetricDelta"] {{
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
}}

/* ── Progress bars ───────────────────────────────────── */
.stProgress > div > div > div {{
    border-radius: 20px !important;
    height: 5px !important;
    background: {ACCENT_GRAD} !important;
}}
.stProgress > div > div {{
    border-radius: 20px !important;
    height: 5px !important;
    background: {BORDER_LIGHT} !important;
}}

/* ── Expanders ───────────────────────────────────────── */
[data-testid="stExpander"] {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS} !important;
    overflow: hidden !important;
    transition: border-color 0.15s ease !important;
    background: {BG_CARD} !important;
}}
[data-testid="stExpander"]:hover {{
    border-color: {TEXT_3} !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: {TEXT_2} !important;
}}

/* ── File uploader ───────────────────────────────────── */
[data-testid="stFileUploader"] {{
    border: 2px dashed {BORDER} !important;
    border-radius: {RADIUS} !important;
    transition: all 0.15s ease !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {ACCENT_MUTED} !important;
    background: {ACCENT_LIGHT} !important;
}}

/* ── Alerts ──────────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: {RADIUS_SM} !important;
    font-size: 0.84rem !important;
    border: none !important;
}}
[data-testid="stToast"] {{
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
}}
.stDivider {{ border-color: {BORDER_LIGHT} !important; }}
[data-testid="stCaptionContainer"] {{ font-size: 0.78rem !important; }}

/* ── Pipeline steps ──────────────────────────────────── */
.ac-step {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.85rem;
    font-size: 0.82rem;
    color: {TEXT_2};
    border-radius: {RADIUS_SM};
    margin-bottom: 4px;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}}
.ac-step-num {{
    font-size: 0.65rem;
    font-weight: 700;
    color: {TEXT_3};
    text-transform: uppercase;
    letter-spacing: 0.05em;
    min-width: 3.2rem;
}}
.ac-step-msg {{ flex: 1; font-weight: 500; }}
.ac-step-icon {{ font-size: 0.95rem; min-width: 1.25rem; text-align: center; }}
.ac-step.running {{ background: {ACCENT_LIGHT}; border-color: {ACCENT_MUTED}; }}
.ac-step.running .ac-step-icon {{ color: {ACCENT}; animation: ac-pulse 1.5s ease-in-out infinite; }}
.ac-step.complete {{ background: {GREEN_BG}; border-color: rgba(16,185,129,0.15); }}
.ac-step.complete .ac-step-icon {{ color: {GREEN}; }}
.ac-step.failed {{ background: {RED_BG}; border-color: rgba(239,68,68,0.15); }}
.ac-step.failed .ac-step-icon {{ color: {RED}; }}
@keyframes ac-pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.35; }} }}

/* ━━ Custom component classes ━━━━━━━━━━━━━━━━━━━━━━━━━ */

/* Hero header */
.ac-hero {{
    padding: 1.5rem 0 1.25rem 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1rem;
}}
.ac-hero-title {{
    font-size: 2.6rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    color: {TEXT} !important;
    margin: 0 !important;
    line-height: 1.15 !important;
}}
.ac-hero-title .ac-hero-accent {{
    background: {ACCENT_GRAD};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.ac-hero-sub {{
    font-size: 0.84rem;
    color: {TEXT_3};
    font-weight: 400;
    margin: 0.35rem 0 0 0;
    letter-spacing: -0.005em;
}}

/* Sidebar brand */
.ac-brand {{
    padding: 0.75rem 0.5rem 1rem 0.5rem;
    margin-bottom: 1.25rem;
    border-bottom: 1px solid {SIDEBAR_BORDER};
}}
.ac-brand-logo {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin-bottom: 0.3rem;
}}
.ac-brand-icon {{
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: {ACCENT_GRAD};
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    color: white;
    font-weight: 800;
    letter-spacing: -0.05em;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}}
.ac-brand-name {{
    font-size: 1.05rem;
    font-weight: 800;
    color: #F1F5F9;
    letter-spacing: -0.03em;
    line-height: 1;
}}
.ac-brand-tag {{
    font-size: 0.7rem;
    color: {SIDEBAR_DIM};
    font-weight: 400;
    margin: 0;
    padding-left: calc(34px + 0.65rem);
    line-height: 1.3;
}}

/* Sidebar section labels */
.ac-label {{
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {SIDEBAR_DIM};
    margin: 1.25rem 0.5rem 0.5rem 0.5rem;
    padding: 0;
}}

/* Sidebar stat cards */
.ac-stat {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0.85rem;
    border-radius: {RADIUS_SM};
    background: {SIDEBAR_CARD};
    border: 1px solid {SIDEBAR_BORDER};
    margin-bottom: 0.3rem;
    transition: background 0.15s ease;
}}
.ac-stat:hover {{
    background: rgba(255,255,255,0.09);
}}
.ac-stat-label {{
    font-size: 0.73rem;
    font-weight: 500;
    color: {SIDEBAR_TEXT};
}}
.ac-stat-val {{
    font-size: 1.05rem;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
}}
.ac-stat-val.accent {{ color: #A78BFA; }}

/* Sidebar tier bar */
.ac-tier {{
    padding: 0.4rem 0.85rem;
    font-size: 0.73rem;
    color: {SIDEBAR_TEXT};
}}
.ac-tier-bar {{
    height: 4px;
    border-radius: 4px;
    background: rgba(255,255,255,0.06);
    margin-top: 4px;
    overflow: hidden;
}}
.ac-tier-fill {{
    height: 100%;
    border-radius: 4px;
    background: {ACCENT_GRAD};
    transition: width 0.4s ease;
}}

/* Empty state */
.ac-empty {{
    text-align: center;
    padding: 2.5rem 1.5rem;
}}
.ac-empty-icon {{
    font-size: 2rem;
    margin-bottom: 0.6rem;
    opacity: 0.35;
}}
.ac-empty-title {{
    font-size: 0.88rem;
    font-weight: 600;
    color: {TEXT_2};
    margin-bottom: 0.25rem;
}}
.ac-empty-desc {{
    font-size: 0.78rem;
    color: {TEXT_3};
    line-height: 1.55;
    max-width: 260px;
    margin: 0 auto;
}}
/* Dark sidebar empty state */
.ac-empty-dark {{
    text-align: center;
    padding: 2rem 0.75rem;
}}
.ac-empty-dark .ac-empty-icon {{ opacity: 0.25; }}
.ac-empty-dark .ac-empty-title {{ color: {SIDEBAR_TEXT}; font-size: 0.85rem; }}
.ac-empty-dark .ac-empty-desc {{ color: {SIDEBAR_DIM}; max-width: 220px; margin: 0 auto; }}

/* Config pill */
.ac-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.25rem 0.65rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    background: {ACCENT_LIGHT};
    color: {ACCENT};
    border: 1px solid {ACCENT_MUTED};
    margin-top: 0.5rem;
    white-space: nowrap;
}}

/* Section heading inside main */
.ac-section-heading {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {TEXT_3};
    margin: 1.5rem 0 0.6rem 0;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid {BORDER_LIGHT};
}}

/* Footer */
.ac-footer {{
    text-align: center;
    color: {TEXT_3};
    font-size: 0.73rem;
    padding: 1.5rem 0 0.75rem 0;
    border-top: 1px solid {BORDER_LIGHT};
    margin-top: 2rem;
    letter-spacing: -0.01em;
}}
.ac-footer a {{
    color: {ACCENT};
    text-decoration: none;
    font-weight: 600;
}}
.ac-footer a:hover {{ color: {ACCENT_HOVER}; }}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session defaults ──────────────────────────────────────────────────────────
for k, v in {
    "active_campaign_id": None,
    "polling_campaign_id": None,
    "_refresh_campaigns": False,
    "_refresh_analytics": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar_analytics()

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="ac-hero">
    <p class="ac-hero-title">Ad<span class="ac-hero-accent">Camp</span></p>
    <p class="ac-hero-sub">AI-powered video ad generation at scale</p>
</div>
""",
    unsafe_allow_html=True,
)

tab_video, tab_campaign = st.tabs(["Quick Video", "Campaign Batch"])

with tab_video:
    render_quick_video()

with tab_campaign:
    render_campaign_batch()

st.divider()
render_campaign_history()

st.markdown(
    f"""
<div class="ac-footer">
    AdCamp v2.0 &middot; Powered by BytePlus ModelArk &middot;
    <a href="{API_BASE}/docs" target="_blank">API Docs</a>
</div>
""",
    unsafe_allow_html=True,
)
