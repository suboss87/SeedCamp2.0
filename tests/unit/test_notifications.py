"""Tests for the notification service.

All tests mock httpx — no real network calls.
Verifies: event routing, webhook payload, Slack formatting, disabled state.
"""

from unittest.mock import AsyncMock, patch

from app.services.notifications import NotificationEvent, notify


class TestNotify:
    @patch("app.services.notifications.settings")
    async def test_disabled_notifications_no_op(self, mock_settings):
        """When notifications are disabled, nothing is sent."""
        mock_settings.notification_enabled = False

        # Should not raise and not call any backend
        await notify(
            NotificationEvent.batch_complete,
            {"campaign_id": "c1", "message": "done"},
        )

    @patch("app.services.notifications.httpx.AsyncClient")
    @patch("app.services.notifications.settings")
    async def test_webhook_sent(self, mock_settings, mock_client_cls):
        """Webhook sends correct payload."""
        mock_settings.notification_enabled = True
        mock_settings.webhook_url = "https://hooks.example.com/notify"
        mock_settings.slack_webhook_url = ""

        mock_client = AsyncMock()
        mock_client.post = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await notify(
            NotificationEvent.batch_complete,
            {"campaign_id": "c1", "message": "3 completed"},
        )

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args.args[0] == "https://hooks.example.com/notify"
        body = call_args.kwargs["json"]
        assert body["event"] == "batch_complete"
        assert body["data"]["campaign_id"] == "c1"

    @patch("app.services.notifications.httpx.AsyncClient")
    @patch("app.services.notifications.settings")
    async def test_slack_sent(self, mock_settings, mock_client_cls):
        """Slack webhook sends formatted message."""
        mock_settings.notification_enabled = True
        mock_settings.webhook_url = ""
        mock_settings.slack_webhook_url = "https://hooks.slack.com/services/xxx"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await notify(
            NotificationEvent.video_failed,
            {"campaign_name": "Summer 2025", "message": "Task timeout"},
        )

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        body = call_args.kwargs["json"]
        assert "Video Failed" in body["text"]
        assert "Summer 2025" in body["text"]

    @patch("app.services.notifications.httpx.AsyncClient")
    @patch("app.services.notifications.settings")
    async def test_webhook_failure_doesnt_raise(self, mock_settings, mock_client_cls):
        """Webhook failure should be logged but not propagated."""
        mock_settings.notification_enabled = True
        mock_settings.webhook_url = "https://hooks.example.com/notify"
        mock_settings.slack_webhook_url = ""

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Should not raise
        await notify(
            NotificationEvent.budget_exceeded,
            {"campaign_id": "c1", "message": "over budget"},
        )

    @patch("app.services.notifications.httpx.AsyncClient")
    @patch("app.services.notifications.settings")
    async def test_both_backends_called(self, mock_settings, mock_client_cls):
        """When both webhook and Slack are configured, both are called."""
        mock_settings.notification_enabled = True
        mock_settings.webhook_url = "https://hooks.example.com/notify"
        mock_settings.slack_webhook_url = "https://hooks.slack.com/services/xxx"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await notify(
            NotificationEvent.video_approved,
            {"campaign_name": "Test", "message": "Approved"},
        )

        # 2 calls: one webhook, one Slack
        assert mock_client.post.call_count == 2

    async def test_all_events_defined(self):
        """All notification events should be valid."""
        events = list(NotificationEvent)
        assert len(events) == 4
        assert NotificationEvent.batch_complete in events
        assert NotificationEvent.video_failed in events
        assert NotificationEvent.budget_exceeded in events
        assert NotificationEvent.video_approved in events
