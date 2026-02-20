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


# Cost labels & targets
COST_LABELS = {"catalog": "$0.08 / video", "hero": "$0.13 / video"}
COST_TARGET_PER_VIDEO = 0.16

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
