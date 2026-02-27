"""
Dashboard Configuration — Design system, API base, and helpers.
"""

import os

API_BASE = os.getenv("API_URL", "http://localhost:8000")

# ── Color System (Enterprise — Blue→Violet) ──────────────────────
ACCENT = "#3B82F6"
ACCENT_HOVER = "#2563EB"
ACCENT_LIGHT = "rgba(59, 130, 246, 0.06)"
ACCENT_MUTED = "rgba(59, 130, 246, 0.14)"
ACCENT_GRAD = "linear-gradient(135deg, #3B82F6 0%, #6366F1 50%, #8B5CF6 100%)"

SIDEBAR_BG = "#0C0A1D"
SIDEBAR_CARD = "rgba(139, 92, 246, 0.07)"
SIDEBAR_BORDER = "rgba(139, 92, 246, 0.14)"
SIDEBAR_TEXT = "#FFFFFF"
SIDEBAR_DIM = "#94949E"

BG_PAGE = "#FAFAFA"
BG_CARD = "#FFFFFF"
BG_SURFACE = "#F5F3FF"
BG_HOVER = "#F3F4F6"

BORDER = "#E5E7EB"
BORDER_LIGHT = "#F3F4F6"

TEXT = "#111111"
TEXT_2 = "#555555"
TEXT_3 = "#999999"

GREEN = "#22C55E"
GREEN_BG = "rgba(34, 197, 94, 0.07)"
RED = "#F43F5E"
RED_BG = "rgba(244, 63, 94, 0.07)"
AMBER = "#F59E0B"
AMBER_BG = "rgba(245, 158, 11, 0.07)"

PLATFORM_COLORS = {
    "tiktok": {
        "bg": "rgba(0,0,0,0.05)",
        "text": "#111111",
        "border": "rgba(0,0,0,0.12)",
    },
    "instagram": {
        "bg": "rgba(225,48,108,0.06)",
        "text": "#C13584",
        "border": "rgba(225,48,108,0.15)",
    },
    "youtube": {
        "bg": "rgba(255,0,0,0.06)",
        "text": "#DC2626",
        "border": "rgba(255,0,0,0.14)",
    },
}


def platform_pill(name: str) -> str:
    c = PLATFORM_COLORS.get(name, {"bg": ACCENT_LIGHT, "text": ACCENT, "border": ACCENT_MUTED})
    label = name.capitalize()
    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.3rem;'
        f"padding:0.2rem 0.55rem;border-radius:14px;font-size:0.72rem;font-weight:600;"
        f'background:{c["bg"]};color:{c["text"]};border:1px solid {c["border"]};">'
        f"{label}</span>"
    )


def platform_pills_html(platforms: list) -> str:
    return " ".join(platform_pill(p) for p in platforms)


SHADOW_SM = "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)"
SHADOW_MD = "0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)"
SHADOW_LG = "0 10px 30px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04)"

RADIUS = "10px"
RADIUS_SM = "7px"
RADIUS_LG = "14px"

# ── Helpers ───────────────────────────────────────────────────────
STEP_ICONS = {"running": "&#9679;", "complete": "&#10003;", "failed": "&#10005;"}


def step_indicator(status: str) -> str:
    return STEP_ICONS.get(status, "&#8211;")


# Cost constants (must match app/config.py)
_COST_PER_M = {"catalog": 1.00, "hero": 1.20}
_RES_MAP = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
_SCRIPT_COST_APPROX = 0.0005  # ~500 input + ~200 output tokens via Seed 1.8


def estimate_cost(tier: str, duration: int = 5, resolution: str = "720p") -> float:
    """Estimate per-video cost using the same formula as pipeline.py."""
    w, h = _RES_MAP.get(resolution, (1280, 720))
    video_tokens = int((w * h * 24 * duration) / 1024)
    cost_per_m = _COST_PER_M.get(tier, 0.70)
    return round((video_tokens / 1_000_000) * cost_per_m + _SCRIPT_COST_APPROX, 4)


def cost_label(tier: str, duration: int = 5, resolution: str = "720p") -> str:
    """Format estimated cost as a display label."""
    return f"~${estimate_cost(tier, duration, resolution):.2f} / video"


COST_TARGET_PER_VIDEO = 0.15

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
