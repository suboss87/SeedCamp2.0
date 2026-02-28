"""
Notifications — Event-driven notification service
Pluggable backends: webhook, Slack. All calls are fire-and-forget.
"""

import logging
from enum import Enum

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class NotificationEvent(str, Enum):
    batch_complete = "batch_complete"
    video_failed = "video_failed"
    budget_exceeded = "budget_exceeded"
    video_approved = "video_approved"


async def notify(event: NotificationEvent, payload: dict):
    """Send notification via configured backends. Non-blocking, never raises."""
    if not settings.notification_enabled:
        return

    logger.info("Sending notification: %s", event.value)

    if settings.webhook_url:
        await _send_webhook(event, payload)

    if settings.slack_webhook_url:
        await _send_slack(event, payload)


async def _send_webhook(event: NotificationEvent, payload: dict):
    """Send generic HTTP POST webhook."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                settings.webhook_url,
                json={"event": event.value, "data": payload},
            )
        logger.info("Webhook sent: %s", event.value)
    except Exception:
        logger.warning("Webhook failed for event %s", event.value, exc_info=True)


async def _send_slack(event: NotificationEvent, payload: dict):
    """Send Slack notification via incoming webhook."""
    _EMOJI = {
        NotificationEvent.batch_complete: ":white_check_mark:",
        NotificationEvent.video_failed: ":x:",
        NotificationEvent.budget_exceeded: ":money_with_wings:",
        NotificationEvent.video_approved: ":thumbsup:",
    }

    emoji = _EMOJI.get(event, ":bell:")
    campaign = payload.get("campaign_name", "Unknown")
    message = payload.get("message", event.value)

    slack_payload = {
        "text": f"{emoji} *AdCamp — {event.value.replace('_', ' ').title()}*\n"
        f"Campaign: {campaign}\n{message}",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(settings.slack_webhook_url, json=slack_payload)
        logger.info("Slack notification sent: %s", event.value)
    except Exception:
        logger.warning("Slack notification failed for event %s", event.value, exc_info=True)
