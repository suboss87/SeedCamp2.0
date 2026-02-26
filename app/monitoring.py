"""
Monitoring and Observability
Prometheus metrics, health checks, and observability utilities.
"""

import time
from typing import Dict, Any
from datetime import datetime, timezone

_start_time = time.time()

# In-memory metrics store (use Redis/Prometheus in production)
# Cost and per-tier video counts are tracked by cost_tracker (single source of truth)
_metrics = {
    "videos_generated_total": 0,
    "videos_failed_total": 0,
    "api_requests_total": 0,
    "safety_checks_total": 0,
    "safety_flagged_total": 0,
    "safety_blocked_total": 0,
    "script_generation_duration_seconds": [],
    "video_generation_duration_seconds": [],
    "safety_eval_duration_seconds": [],
}


def increment_counter(metric: str, value: int = 1):
    """Increment a counter metric."""
    if metric in _metrics:
        _metrics[metric] += value


def record_duration(metric: str, duration_seconds: float):
    """Record a duration metric."""
    if metric in _metrics and isinstance(_metrics[metric], list):
        _metrics[metric].append(duration_seconds)
        # Keep only last 1000 samples
        if len(_metrics[metric]) > 1000:
            _metrics[metric] = _metrics[metric][-1000:]


def _avg(metric_key: str) -> float:
    """Average of a list metric, or 0 if empty."""
    vals = _metrics[metric_key]
    return sum(vals) / len(vals) if vals else 0


def get_metrics() -> Dict[str, Any]:
    """Get current metrics snapshot."""
    from app.services import cost_tracker

    cost_summary = cost_tracker.get_summary()

    return {
        "videos_generated_total": _metrics["videos_generated_total"],
        "videos_failed_total": _metrics["videos_failed_total"],
        "api_requests_total": _metrics["api_requests_total"],
        "script_generation_avg_seconds": round(
            _avg("script_generation_duration_seconds"), 2
        ),
        "video_generation_avg_seconds": round(
            _avg("video_generation_duration_seconds"), 2
        ),
        "safety_checks_total": _metrics["safety_checks_total"],
        "safety_flagged_total": _metrics["safety_flagged_total"],
        "safety_blocked_total": _metrics["safety_blocked_total"],
        "safety_eval_avg_seconds": round(_avg("safety_eval_duration_seconds"), 2),
        "total_cost_usd": cost_summary.total_cost_usd,
        "avg_cost_per_video": cost_summary.avg_cost_per_video,
        "hero_videos": cost_summary.hero_videos,
        "catalog_videos": cost_summary.catalog_videos,
    }


def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": get_metrics(),
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


def prometheus_format() -> str:
    """Format metrics in Prometheus text format."""
    metrics = get_metrics()
    lines = [
        "# HELP videos_generated_total Total number of videos generated",
        "# TYPE videos_generated_total counter",
        f"videos_generated_total {metrics['videos_generated_total']}",
        "",
        "# HELP videos_failed_total Total number of failed video generations",
        "# TYPE videos_failed_total counter",
        f"videos_failed_total {metrics['videos_failed_total']}",
        "",
        "# HELP api_requests_total Total number of API requests",
        "# TYPE api_requests_total counter",
        f"api_requests_total {metrics['api_requests_total']}",
        "",
        "# HELP script_generation_avg_seconds Average script generation duration",
        "# TYPE script_generation_avg_seconds gauge",
        f"script_generation_avg_seconds {metrics['script_generation_avg_seconds']}",
        "",
        "# HELP video_generation_avg_seconds Average video generation duration",
        "# TYPE video_generation_avg_seconds gauge",
        f"video_generation_avg_seconds {metrics['video_generation_avg_seconds']}",
        "",
        "# HELP total_cost_usd Total cost in USD",
        "# TYPE total_cost_usd gauge",
        f"total_cost_usd {metrics['total_cost_usd']}",
        "",
        "# HELP avg_cost_per_video Average cost per video in USD",
        "# TYPE avg_cost_per_video gauge",
        f"avg_cost_per_video {metrics['avg_cost_per_video']}",
        "",
        "# HELP hero_videos_total Total hero videos generated",
        "# TYPE hero_videos_total counter",
        f"hero_videos_total {metrics['hero_videos']}",
        "",
        "# HELP catalog_videos_total Total catalog videos generated",
        "# TYPE catalog_videos_total counter",
        f"catalog_videos_total {metrics['catalog_videos']}",
        "",
        "# HELP safety_checks_total Total safety evaluations performed",
        "# TYPE safety_checks_total counter",
        f"safety_checks_total {metrics['safety_checks_total']}",
        "",
        "# HELP safety_flagged_total Total content flagged by safety eval",
        "# TYPE safety_flagged_total counter",
        f"safety_flagged_total {metrics['safety_flagged_total']}",
        "",
        "# HELP safety_blocked_total Total content blocked by safety eval",
        "# TYPE safety_blocked_total counter",
        f"safety_blocked_total {metrics['safety_blocked_total']}",
        "",
        "# HELP safety_eval_avg_seconds Average safety evaluation duration",
        "# TYPE safety_eval_avg_seconds gauge",
        f"safety_eval_avg_seconds {metrics['safety_eval_avg_seconds']}",
        "",
    ]
    return "\n".join(lines)
