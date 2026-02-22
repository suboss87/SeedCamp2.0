"""
Dashboard Configuration — Design system, API base, and helpers.
"""

import os

API_BASE = os.getenv("API_URL", "http://localhost:8000")

# ── Color System ──────────────────────────────────────────────────
ACCENT = "#6366F1"
ACCENT_HOVER = "#4F46E5"
ACCENT_LIGHT = "rgba(99, 102, 241, 0.08)"
ACCENT_MUTED = "rgba(99, 102, 241, 0.22)"
ACCENT_GRAD = "linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A78BFA 100%)"

SIDEBAR_BG = "#0F172A"
SIDEBAR_CARD = "rgba(255,255,255,0.06)"
SIDEBAR_BORDER = "rgba(255,255,255,0.08)"
SIDEBAR_TEXT = "#CBD5E1"
SIDEBAR_DIM = "#64748B"

BG_PAGE = "#F8FAFC"
BG_CARD = "#FFFFFF"
BG_SURFACE = "#F1F5F9"
BG_HOVER = "#F8FAFC"

BORDER = "#E2E8F0"
BORDER_LIGHT = "#F1F5F9"

TEXT = "#0F172A"
TEXT_2 = "#475569"
TEXT_3 = "#94A3B8"

GREEN = "#10B981"
GREEN_BG = "rgba(16,185,129,0.08)"
RED = "#EF4444"
RED_BG = "rgba(239,68,68,0.08)"
AMBER = "#F59E0B"
AMBER_BG = "rgba(245,158,11,0.08)"

PLATFORM_COLORS = {
    "tiktok": {
        "bg": "rgba(0,0,0,0.06)",
        "text": "#010101",
        "border": "rgba(0,0,0,0.15)",
    },
    "instagram": {
        "bg": "rgba(225,48,108,0.08)",
        "text": "#E1306C",
        "border": "rgba(225,48,108,0.2)",
    },
    "youtube": {
        "bg": "rgba(255,0,0,0.07)",
        "text": "#FF0000",
        "border": "rgba(255,0,0,0.18)",
    },
}


def platform_pill(name: str) -> str:
    c = PLATFORM_COLORS.get(
        name, {"bg": ACCENT_LIGHT, "text": ACCENT, "border": ACCENT_MUTED}
    )
    label = name.capitalize()
    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.3rem;'
        f"padding:0.2rem 0.55rem;border-radius:14px;font-size:0.72rem;font-weight:600;"
        f'background:{c["bg"]};color:{c["text"]};border:1px solid {c["border"]};">'
        f"{label}</span>"
    )


def platform_pills_html(platforms: list) -> str:
    return " ".join(platform_pill(p) for p in platforms)


SHADOW_SM = "0 1px 2px rgba(0,0,0,0.04)"
SHADOW_MD = "0 2px 8px rgba(0,0,0,0.06)"
SHADOW_LG = "0 8px 24px rgba(0,0,0,0.08)"

RADIUS = "12px"
RADIUS_SM = "8px"
RADIUS_LG = "16px"

# ── Helpers ───────────────────────────────────────────────────────
STEP_ICONS = {"running": "&#9679;", "complete": "&#10003;", "failed": "&#10005;"}


def step_indicator(status: str) -> str:
    return STEP_ICONS.get(status, "&#8211;")


# Cost constants (must match app/config.py)
_COST_PER_M = {"catalog": 0.70, "hero": 1.20}
_RES_MAP = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
_SCRIPT_COST_APPROX = 0.001


def estimate_cost(tier: str, duration: int = 5, resolution: str = "720p") -> float:
    """Estimate per-video cost using the same formula as pipeline.py."""
    w, h = _RES_MAP.get(resolution, (1280, 720))
    video_tokens = int((w * h * 24 * duration) / 1024)
    cost_per_m = _COST_PER_M.get(tier, 0.70)
    return round((video_tokens / 1_000_000) * cost_per_m + _SCRIPT_COST_APPROX, 4)


def cost_label(tier: str, duration: int = 5, resolution: str = "720p") -> str:
    """Format estimated cost as a display label."""
    return f"~${estimate_cost(tier, duration, resolution):.2f} / video"


COST_TARGET_PER_VIDEO = 0.09

STATUS_COLORS = {
    "draft": "gray",
    "generating": "violet",
    "completed": "green",
    "partial": "orange",
    "failed": "red",
    "pending": "gray",
}


def status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "gray")
    return f":{color}[{status.upper()}]"
