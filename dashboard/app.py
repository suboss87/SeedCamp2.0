"""
AdCamp — AI Video Ad Generation Dashboard
"""

import streamlit as st
from sections import (
    render_campaign_batch,
    render_campaign_history,
    render_quick_video,
    render_sidebar_analytics,
)

from config import (
    ACCENT,
    ACCENT_GRAD,
    ACCENT_HOVER,
    ACCENT_LIGHT,
    ACCENT_MUTED,
    API_BASE,
    BG_CARD,
    BG_HOVER,
    BG_PAGE,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    GREEN,
    GREEN_BG,
    RADIUS,
    RADIUS_SM,
    RED,
    RED_BG,
    SHADOW_MD,
    SHADOW_SM,
    SIDEBAR_BG,
    SIDEBAR_BORDER,
    SIDEBAR_CARD,
    SIDEBAR_DIM,
    SIDEBAR_TEXT,
    TEXT,
    TEXT_2,
    TEXT_3,
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
    -moz-osx-font-smoothing: grayscale;
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
    padding: 1.5rem 2.5rem 2rem 2.5rem !important;
    max-width: 1140px !important;
}}

/* ── Hide Streamlit chrome ───────────────────────────── */
#MainMenu, footer, .stDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"] {{ display: none !important; }}
header[data-testid="stHeader"] {{
    background: transparent !important;
    backdrop-filter: none !important;
    height: 2.25rem !important;
    overflow: visible !important;
}}

/* ── Typography ──────────────────────────────────────── */
[data-testid="stMain"] h1 {{ font-weight: 800 !important; letter-spacing: -0.035em !important; font-size: 1.35rem !important; line-height: 1.2 !important; color: {TEXT} !important; }}
[data-testid="stMain"] h2 {{ font-weight: 700 !important; letter-spacing: -0.025em !important; font-size: 1.15rem !important; color: {TEXT} !important; margin-top: 0.1rem !important; }}
[data-testid="stMain"] h3 {{ font-weight: 700 !important; letter-spacing: -0.02em !important; font-size: 1rem !important; color: {TEXT} !important; }}
[data-testid="stMain"] h4 {{ font-weight: 600 !important; letter-spacing: -0.015em !important; font-size: 0.92rem !important; color: {TEXT_2} !important; }}
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

/* ── SIDEBAR — Deep violet-black ─────────────────────── */
section[data-testid="stSidebar"] {{
    background: {SIDEBAR_BG} !important;
    border-right: 1px solid rgba(139, 92, 246, 0.08) !important;
    box-shadow: none !important;
}}
section[data-testid="stSidebar"] .block-container {{
    padding: 1.15rem 1.15rem !important;
}}
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}}
/* ── Sidebar toggle arrows — ALWAYS visible ────────── */
section[data-testid="stSidebar"] button[kind="header"],
section[data-testid="stSidebar"] [data-testid="baseButton-header"] {{
    background: rgba(139, 92, 246, 0.12) !important;
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
    border-radius: 7px !important;
    box-shadow: none !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    width: 30px !important;
    height: 30px !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    position: relative !important;
    z-index: 100 !important;
}}
section[data-testid="stSidebar"] button[kind="header"]:hover,
section[data-testid="stSidebar"] [data-testid="baseButton-header"]:hover {{
    background: rgba(139, 92, 246, 0.2) !important;
}}
section[data-testid="stSidebar"] button[kind="header"] svg,
section[data-testid="stSidebar"] [data-testid="baseButton-header"] svg {{
    fill: {SIDEBAR_TEXT} !important;
    color: {SIDEBAR_TEXT} !important;
    width: 18px !important;
    height: 18px !important;
}}
/* Expand arrow when sidebar is collapsed */
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
    border: 1px solid {BORDER} !important;
    border-radius: 7px !important;
    box-shadow: {SHADOW_SM} !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    width: 34px !important;
    height: 34px !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: background 0.12s ease !important;
}}
[data-testid="collapsedControl"] button:hover,
[data-testid="collapsedControl"] [data-testid="baseButton-header"]:hover {{
    background: {BG_SURFACE} !important;
    box-shadow: {SHADOW_MD} !important;
}}
[data-testid="collapsedControl"] svg {{
    fill: {TEXT_2} !important;
    color: {TEXT_2} !important;
    width: 18px !important;
    height: 18px !important;
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
    color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] .stProgress > div > div {{
    background: rgba(139, 92, 246, 0.1) !important;
}}
section[data-testid="stSidebar"] .stProgress > div > div > div {{
    background: {ACCENT_GRAD} !important;
}}
section[data-testid="stSidebar"] .stButton > button {{
    background: rgba(139, 92, 246, 0.08) !important;
    border: 1px solid rgba(139, 92, 246, 0.15) !important;
    color: {SIDEBAR_TEXT} !important;
    border-radius: {RADIUS_SM} !important;
    font-weight: 500 !important;
    font-size: 0.78rem !important;
    transition: all 0.12s ease !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(139, 92, 246, 0.15) !important;
    border-color: rgba(139, 92, 246, 0.25) !important;
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
    transition: box-shadow 0.15s ease, border-color 0.15s ease !important;
    overflow: hidden !important;
    background: {BG_CARD} !important;
}}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlockBorderWrapper"][style*="border"]:hover {{
    box-shadow: {SHADOW_MD} !important;
    border-color: #D1D5DB !important;
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
    background-color: #EDEAF5 !important;
    border-radius: 10px !important;
    display: inline-flex !important;
    width: auto !important;
    border: 1px solid #DDD8EC !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    display: none !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: -0.01em !important;
    padding: 0.5rem 1.35rem !important;
    border-radius: 7px !important;
    border-bottom: none !important;
    color: {TEXT_2} !important;
    transition: all 0.12s ease !important;
    margin-bottom: 0 !important;
    background: transparent !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] p {{
    color: inherit !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {{
    color: {TEXT} !important;
    background: rgba(255,255,255,0.5) !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {ACCENT} !important;
    font-weight: 700 !important;
    border-bottom: none !important;
    background: {BG_CARD} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04) !important;
}}
[data-testid="stTabs"] [aria-selected="true"] p {{
    color: {ACCENT} !important;
}}
[data-testid="stTabContent"] {{
    padding-top: 0.85rem !important;
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
    background: {ACCENT} !important;
    color: #FFFFFF !important;
    border: none !important;
}}
[data-testid="stMain"] [data-baseweb="tag"] span,
[data-testid="stMain"] [data-baseweb="tag"] svg,
[data-testid="stMain"] [data-baseweb="tag"] div {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}
[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
    background: {ACCENT} !important;
    color: #FFFFFF !important;
    border: none !important;
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
    padding: 0.65rem 0.85rem !important;
    font-size: 0.85rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.12s ease, box-shadow 0.12s ease !important;
    background-color: {BG_CARD} !important;
    color: {TEXT} !important;
    line-height: 1.5 !important;
}}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT_LIGHT} !important;
    outline: none !important;
}}
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label {{
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    color: {TEXT_2} !important;
    letter-spacing: -0.01em !important;
}}

/* ── Selects & multiselects ──────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_SM} !important;
    font-size: 0.85rem !important;
    transition: border-color 0.12s ease !important;
    background-color: {BG_CARD} !important;
    color: {TEXT} !important;
}}
[data-testid="stSelectbox"] > div > div:hover,
[data-testid="stMultiSelect"] > div > div:hover {{
    border-color: #D1D5DB !important;
}}
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    color: {TEXT_2} !important;
}}
[data-testid="stSelectbox"] svg,
[data-testid="stMultiSelect"] svg {{
    fill: {TEXT_3} !important;
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
    font-size: 0.85rem !important;
}}
[data-testid="stMain"] [data-testid="stCheckbox"] span[data-baseweb="checkbox"] {{
    border-color: #D1D5DB !important;
    border-width: 1.5px !important;
    border-radius: 4px !important;
    width: 18px !important;
    height: 18px !important;
}}
[data-testid="stMain"] [data-testid="stCheckbox"] input:checked + span[data-baseweb="checkbox"] {{
    background: {ACCENT} !important;
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

/* ── Primary button — Solid, confident ───────────────── */
.stButton > button[kind="primary"] {{
    background: {ACCENT} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 0.55rem 1.3rem !important;
    box-shadow: none !important;
    transition: all 0.12s ease !important;
    letter-spacing: -0.01em !important;
}}
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {{
    color: #FFFFFF !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: {ACCENT_HOVER} !important;
    box-shadow: 0 2px 6px rgba(59, 130, 246, 0.2) !important;
}}
.stButton > button[kind="primary"]:active {{
    background: #1D4ED8 !important;
}}

/* ── Secondary button ────────────────────────────────── */
.stButton > button[kind="secondary"],
.stButton > button:not([kind]) {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: {TEXT_2} !important;
    background: {BG_CARD} !important;
    transition: all 0.12s ease !important;
    padding: 0.5rem 1.15rem !important;
}}
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind]):hover {{
    border-color: #D1D5DB !important;
    color: {TEXT} !important;
    background: {BG_HOVER} !important;
}}

/* ── Link buttons ────────────────────────────────────── */
.stLinkButton > a {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    transition: all 0.12s ease !important;
}}
.stLinkButton > a:hover {{
    border-color: #D1D5DB !important;
    color: {TEXT} !important;
}}

/* ── Metrics ─────────────────────────────────────────── */
[data-testid="stMetricLabel"] {{
    font-family: 'Inter', sans-serif !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    color: {TEXT_3} !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    font-size: 1.3rem !important;
    font-variant-numeric: tabular-nums !important;
}}
[data-testid="stMetricDelta"] {{
    font-family: 'Inter', sans-serif !important;
    font-size: 0.73rem !important;
    font-weight: 500 !important;
}}

/* ── Progress bars ───────────────────────────────────── */
.stProgress > div > div > div {{
    border-radius: 20px !important;
    height: 4px !important;
    background: {ACCENT} !important;
}}
.stProgress > div > div {{
    border-radius: 20px !important;
    height: 4px !important;
    background: {BORDER_LIGHT} !important;
}}

/* ── Expanders ───────────────────────────────────────── */
[data-testid="stExpander"] {{
    border: 1px solid {BORDER} !important;
    border-radius: {RADIUS} !important;
    overflow: hidden !important;
    transition: border-color 0.12s ease !important;
    background: {BG_CARD} !important;
}}
[data-testid="stExpander"]:hover {{
    border-color: #D1D5DB !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    color: {TEXT_2} !important;
}}

/* ── File uploader ───────────────────────────────────── */
[data-testid="stFileUploader"] {{
    border: 1.5px dashed {BORDER} !important;
    border-radius: {RADIUS} !important;
    transition: all 0.12s ease !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {ACCENT_MUTED} !important;
    background: {ACCENT_LIGHT} !important;
}}

/* ── Alerts ──────────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: {RADIUS_SM} !important;
    font-size: 0.83rem !important;
    border: none !important;
}}
[data-testid="stToast"] {{
    border-radius: {RADIUS_SM} !important;
    font-family: 'Inter', sans-serif !important;
}}
.stDivider {{ border-color: {BORDER_LIGHT} !important; }}
[data-testid="stCaptionContainer"] {{ font-size: 0.76rem !important; }}

/* ── Pipeline steps ──────────────────────────────────── */
.ac-step {{
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0.8rem;
    font-size: 0.8rem;
    color: {TEXT_2};
    border-radius: {RADIUS_SM};
    margin-bottom: 3px;
    transition: all 0.15s ease;
    border: 1px solid transparent;
}}
.ac-step-num {{
    font-size: 0.62rem;
    font-weight: 700;
    color: {TEXT_3};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    min-width: 3rem;
}}
.ac-step-msg {{ flex: 1; font-weight: 500; }}
.ac-step-icon {{ font-size: 0.9rem; min-width: 1.2rem; text-align: center; }}
.ac-step.running {{ background: {ACCENT_LIGHT}; border-color: {ACCENT_MUTED}; }}
.ac-step.running .ac-step-icon {{ color: {ACCENT}; animation: ac-pulse 1.5s ease-in-out infinite; }}
.ac-step.complete {{ background: {GREEN_BG}; border-color: rgba(34,197,94,0.12); }}
.ac-step.complete .ac-step-icon {{ color: {GREEN}; }}
.ac-step.failed {{ background: {RED_BG}; border-color: rgba(244,63,94,0.12); }}
.ac-step.failed .ac-step-icon {{ color: {RED}; }}
@keyframes ac-pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}

/* ━━ Custom component classes ━━━━━━━━━━━━━━━━━━━━━━━━━ */

/* Hero header */
.ac-hero {{
    padding: 0.75rem 0 0.65rem 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 0.65rem;
}}
.ac-hero-title {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.035em !important;
    color: {TEXT} !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}}
.ac-hero-title .ac-hero-accent {{
    color: {ACCENT};
}}
.ac-hero-sub {{
    font-size: 0.78rem;
    color: {TEXT_3};
    font-weight: 400;
    margin: 0.15rem 0 0 0;
    letter-spacing: -0.005em;
}}

/* Sidebar brand */
.ac-brand {{
    padding: 0 0.5rem 0.75rem 0.5rem;
    margin-top: -0.5rem;
    margin-bottom: 1.15rem;
    border-bottom: 1px solid {SIDEBAR_BORDER};
}}
.ac-brand-logo {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
}}
.ac-brand-icon {{
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: {ACCENT_GRAD};
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: white;
    font-weight: 800;
    letter-spacing: -0.05em;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}}
.ac-brand-text {{
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}}
.ac-brand-name {{
    font-size: 1.1rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.03em;
    line-height: 1;
}}
.ac-brand-sub {{
    font-size: 0.7rem;
    color: {SIDEBAR_DIM};
    font-weight: 400;
    line-height: 1.2;
    letter-spacing: 0;
}}

/* Sidebar section labels */
.ac-label {{
    font-size: 0.58rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {SIDEBAR_DIM};
    margin: 1.15rem 0.5rem 0.45rem 0.5rem;
    padding: 0;
}}

/* Sidebar stat cards */
.ac-stat {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.55rem 0.75rem;
    border-radius: {RADIUS_SM};
    background: {SIDEBAR_CARD};
    border: 1px solid {SIDEBAR_BORDER};
    margin-bottom: 0.25rem;
    transition: background 0.12s ease;
}}
.ac-stat:hover {{
    background: rgba(139, 92, 246, 0.12);
}}
.ac-stat-label {{
    font-size: 0.72rem;
    font-weight: 500;
    color: {SIDEBAR_TEXT};
}}
.ac-stat-val {{
    font-size: 1rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
}}
.ac-stat-val.accent {{ color: {ACCENT}; }}

/* Sidebar tier bar */
.ac-tier {{
    padding: 0.35rem 0.75rem;
    font-size: 0.72rem;
    color: {SIDEBAR_TEXT};
}}
.ac-tier-bar {{
    height: 3px;
    border-radius: 3px;
    background: rgba(139, 92, 246, 0.08);
    margin-top: 3px;
    overflow: hidden;
}}
.ac-tier-fill {{
    height: 100%;
    border-radius: 3px;
    background: {ACCENT_GRAD};
    transition: width 0.3s ease;
}}

/* Empty state */
.ac-empty {{
    text-align: center;
    padding: 1.5rem 1.25rem;
}}
.ac-empty-icon {{
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
    opacity: 0.3;
}}
.ac-empty-title {{
    font-size: 0.85rem;
    font-weight: 600;
    color: {TEXT_2};
    margin-bottom: 0.2rem;
}}
.ac-empty-desc {{
    font-size: 0.76rem;
    color: {TEXT_3};
    line-height: 1.5;
    max-width: 260px;
    margin: 0 auto;
}}
/* Dark sidebar empty state */
.ac-empty-dark {{
    text-align: center;
    padding: 1.75rem 0.75rem;
}}
.ac-empty-dark .ac-empty-icon {{ opacity: 0.2; }}
.ac-empty-dark .ac-empty-title {{ color: {SIDEBAR_TEXT}; font-size: 0.82rem; }}
.ac-empty-dark .ac-empty-desc {{ color: {SIDEBAR_DIM}; max-width: 220px; margin: 0 auto; }}

/* Config pill */
.ac-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    background: {ACCENT_LIGHT};
    color: {ACCENT};
    border: 1px solid {ACCENT_MUTED};
    margin-top: 0.4rem;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}}

/* Section heading inside main */
.ac-section-heading {{
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: {TEXT_3};
    margin: 1.25rem 0 0.5rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid {BORDER_LIGHT};
}}

/* Footer */
.ac-footer {{
    text-align: center;
    color: {TEXT_3};
    font-size: 0.72rem;
    padding: 0.85rem 0 0.5rem 0;
    border-top: 1px solid {BORDER_LIGHT};
    margin-top: 1.25rem;
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
