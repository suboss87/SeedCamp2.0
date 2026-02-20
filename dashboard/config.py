"""
Dashboard Configuration — shared across all pages.
Design system tokens, API base URL, and helper functions.
"""
import os

API_BASE = os.getenv(
    "API_URL",
    "http://localhost:8000",
)

# ─── Design System (Linear / Vercel inspired) ────────────────────────────────

# Palette
ACCENT = "#6366F1"          # Indigo-500
ACCENT_HOVER = "#4F46E5"    # Indigo-600
ACCENT_LIGHT = "#EEF2FF"    # Indigo-50
ACCENT_MUTED = "#C7D2FE"    # Indigo-200

# Neutrals
TEXT_PRIMARY = "#0F172A"     # Slate-900
TEXT_SECONDARY = "#64748B"   # Slate-500
TEXT_TERTIARY = "#94A3B8"    # Slate-400
BORDER = "#E2E8F0"           # Slate-200
BORDER_SUBTLE = "#F1F5F9"   # Slate-100

# Status
SUCCESS = "#10B981"          # Emerald-500
SUCCESS_LIGHT = "#ECFDF5"
WARNING = "#F59E0B"          # Amber-500
WARNING_LIGHT = "#FFFBEB"
ERROR = "#EF4444"            # Red-500
ERROR_LIGHT = "#FEF2F2"

# Elevation
SHADOW_SM = "0 1px 2px 0 rgba(0,0,0,0.05)"
SHADOW_MD = "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)"

# Step indicators (used by quick_test.py pipeline steps)
_STEP_INDICATORS = {
    "running": "&#9679;",   # Filled circle
    "complete": "&#10003;",  # Checkmark
    "failed": "&#10005;",   # X mark
}


def step_indicator(status: str) -> str:
    return _STEP_INDICATORS.get(status, "&#8211;")


# Cost estimation (dynamic — reacts to tier, duration, resolution)
# Resolution → pixel dimensions (matches app/services/pipeline.py:20)
_RES_MAP = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
# Cost per million tokens by tier (matches app/config.py:21-22)
_COST_PER_M = {"catalog": 0.70, "hero": 1.20}
# Fixed estimate for script generation cost (~Seed 1.8)
_SCRIPT_COST_EST = 0.002


def estimate_video_cost(tier: str, duration: int, resolution: str) -> float:
    """Estimate total cost using BytePlus token formula.
    Formula: (W × H × FPS × Duration) / 1024 → tokens
    Cost:    tokens / 1,000,000 × cost_per_M + script_estimate
    """
    w, h = _RES_MAP.get(resolution, (1280, 720))
    fps = 24
    video_tokens = (w * h * fps * duration) / 1024
    cost_per_m = _COST_PER_M.get(tier, 0.70)
    video_cost = (video_tokens / 1_000_000) * cost_per_m
    return round(video_cost + _SCRIPT_COST_EST, 4)


COST_TARGET_PER_VIDEO = 0.33

# Native Streamlit status badges (replaces status_badge_html)
STATUS_COLORS = {
    "draft": "gray",
    "generating": "violet",
    "completed": "green",
    "partial": "orange",
    "failed": "red",
    "pending": "gray",
}


def status_badge(status: str) -> str:
    """Render a native Streamlit colored status badge."""
    color = STATUS_COLORS.get(status, "gray")
    return f":{color}[{status.upper()}]"
