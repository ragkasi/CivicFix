"""Notification service tests.

All tests run without sending real emails or SMS.
External provider calls are mocked via unittest.mock.patch.
DB-dependent tests skip when SUPABASE_URL is not configured.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.services.notification_service import build_resident_message, build_subject

_settings = get_settings()
_db_configured = bool(_settings.supabase_url and _settings.supabase_service_role_key)
_requires_db = pytest.mark.skipif(
    not _db_configured, reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set"
)


# ─── Pure function tests — always run ─────────────────────────────────────────


def test_build_resident_message_includes_status():
    msg = build_resident_message("in_progress")
    assert "working" in msg.lower() or "progress" in msg.lower() or "crew" in msg.lower()


def test_build_resident_message_includes_public_note():
    msg = build_resident_message("reviewed", public_note="Crew scheduled for Tuesday.")
    assert "Crew scheduled for Tuesday." in msg


def test_build_resident_message_without_note():
    msg = build_resident_message("resolved")
    assert "resolved" in msg.lower() or "thank" in msg.lower()


def test_build_resident_message_unknown_status():
    msg = build_resident_message("some_future_status")
    assert "some future status" in msg.lower() or "updated" in msg.lower()


def test_build_subject_includes_status_label():
    subject = build_subject("in_progress")
    assert "In Progress" in subject or "CivicFix" in subject


# ─── Service tests — mocked providers ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_status_update_returns_empty_without_db():
    """Without Supabase configured, send_status_update returns empty list gracefully."""
    from app.services.notification_service import NotificationService
    svc = NotificationService()

    with patch("app.services.notification_service.get_supabase_client") as mock:
        mock.side_effect = RuntimeError("Not configured")
        results = await svc.send_status_update("test-report-id", "reviewed")

    assert results == []


@pytest.mark.asyncio
async def test_send_status_update_skips_when_no_contact_info():
    """Reports with no contact info return a skipped result."""
    from app.services.notification_service import NotificationService
    svc = NotificationService()

    mock_row = {"id": "uuid1", "status": "reviewed", "contact_email": None, "contact_phone": None}
    mock_res = MagicMock()
    mock_res.data = [mock_row]

    with patch("app.services.notification_service.get_supabase_client") as mock_client:
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_res
        mock_client.return_value = mock_sb
        results = await svc.send_status_update("uuid1", "reviewed")

    assert len(results) == 1
    assert results[0].status == "skipped"


@pytest.mark.asyncio
async def test_send_mock_email_when_no_provider():
    """Without EMAIL_PROVIDER config, email is mock-sent with is_mock=True."""
    from app.services.notification_service import NotificationService
    svc = NotificationService()

    mock_row = {"id": "uuid1", "status": "reviewed", "contact_email": "test@example.com", "contact_phone": None}
    mock_res = MagicMock()
    mock_res.data = [mock_row]
    mock_log = MagicMock()
    mock_log.data = []

    with patch("app.services.notification_service.get_supabase_client") as mock_client, \
         patch("app.services.notification_service.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            email_provider="", email_api_key="", email_from="noreply@test.com",
            twilio_account_sid="", twilio_auth_token="", twilio_phone_number="",
        )
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_res
        mock_sb.table.return_value.insert.return_value.execute.return_value = mock_log
        mock_client.return_value = mock_sb

        results = await svc.send_status_update("uuid1", "reviewed")

    assert len(results) == 1
    assert results[0].channel == "email"
    assert results[0].is_mock is True
    assert results[0].status == "sent"


@pytest.mark.asyncio
async def test_send_mock_sms_when_no_twilio():
    """Without Twilio config, SMS is mock-sent with is_mock=True."""
    from app.services.notification_service import NotificationService
    svc = NotificationService()

    mock_row = {"id": "uuid1", "status": "in_progress", "contact_email": None, "contact_phone": "+15550001234"}
    mock_res = MagicMock()
    mock_res.data = [mock_row]
    mock_log = MagicMock()
    mock_log.data = []

    with patch("app.services.notification_service.get_supabase_client") as mock_client, \
         patch("app.services.notification_service.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            email_provider="", email_api_key="", email_from="noreply@test.com",
            twilio_account_sid="", twilio_auth_token="", twilio_phone_number="",
        )
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_res
        mock_sb.table.return_value.insert.return_value.execute.return_value = mock_log
        mock_client.return_value = mock_sb

        results = await svc.send_status_update("uuid1", "in_progress")

    assert len(results) == 1
    assert results[0].channel == "sms"
    assert results[0].is_mock is True


@pytest.mark.asyncio
async def test_resend_email_sends_real_call():
    """With email_provider=resend, the service calls the Resend API."""
    from app.services.notification_service import NotificationService
    svc = NotificationService()

    mock_row = {"id": "uuid1", "status": "resolved", "contact_email": "test@example.com", "contact_phone": None}
    mock_res = MagicMock()
    mock_res.data = [mock_row]
    mock_log = MagicMock()
    mock_log.data = []
    mock_http_resp = MagicMock()
    mock_http_resp.json.return_value = {"id": "email-abc"}
    mock_http_resp.raise_for_status = MagicMock()

    with patch("app.services.notification_service.get_supabase_client") as mock_client, \
         patch("app.services.notification_service.get_settings") as mock_settings, \
         patch("app.services.notification_service.httpx.AsyncClient") as MockHttp:
        mock_settings.return_value = MagicMock(
            email_provider="resend", email_api_key="re_test_key",
            email_from="noreply@test.com",
            twilio_account_sid="", twilio_auth_token="", twilio_phone_number="",
        )
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_res
        mock_sb.table.return_value.insert.return_value.execute.return_value = mock_log
        mock_client.return_value = mock_sb

        mock_http_instance = AsyncMock()
        mock_http_instance.__aenter__ = AsyncMock(return_value=mock_http_instance)
        mock_http_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http_instance.post = AsyncMock(return_value=mock_http_resp)
        MockHttp.return_value = mock_http_instance

        results = await svc.send_status_update("uuid1", "resolved")

    assert len(results) == 1
    assert results[0].is_mock is False
    assert results[0].status == "sent"


@pytest.mark.asyncio
async def test_email_provider_failure_returns_failed_status():
    """Provider HTTP failure returns status='failed', does not raise."""
    from app.services.notification_service import NotificationService
    svc = NotificationService()

    mock_row = {"id": "uuid1", "status": "reviewed", "contact_email": "test@example.com", "contact_phone": None}
    mock_res = MagicMock()
    mock_res.data = [mock_row]
    mock_log = MagicMock()
    mock_log.data = []

    with patch("app.services.notification_service.get_supabase_client") as mock_client, \
         patch("app.services.notification_service.get_settings") as mock_settings, \
         patch("app.services.notification_service.httpx.AsyncClient") as MockHttp:
        mock_settings.return_value = MagicMock(
            email_provider="resend", email_api_key="bad_key",
            email_from="noreply@test.com",
            twilio_account_sid="", twilio_auth_token="", twilio_phone_number="",
        )
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_res
        mock_sb.table.return_value.insert.return_value.execute.return_value = mock_log
        mock_client.return_value = mock_sb

        mock_http_instance = AsyncMock()
        mock_http_instance.__aenter__ = AsyncMock(return_value=mock_http_instance)
        mock_http_instance.__aexit__ = AsyncMock(return_value=False)
        mock_http_instance.post = AsyncMock(side_effect=Exception("Network error"))
        MockHttp.return_value = mock_http_instance

        results = await svc.send_status_update("uuid1", "reviewed")

    assert results[0].status == "failed"
    assert results[0].error is not None


# ─── API-level tests — always run ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_endpoint_returns_200_for_unknown_report(client: AsyncClient):
    """For an unknown report, notify returns 200 with empty/skipped results or 503."""
    response = await client.post(f"/api/reports/{uuid.uuid4()}/notify", json={})
    assert response.status_code in (200, 503)


@pytest.mark.asyncio
async def test_status_update_still_returns_quickly(client: AsyncClient):
    """PATCH /status returns 404 for unknown ID (background task is scheduled but ID check happens)."""
    response = await client.patch(
        f"/api/reports/{uuid.uuid4()}/status",
        json={"status": "reviewed"},
    )
    assert response.status_code in (404, 503)


# ─── DB integration — skip without credentials ────────────────────────────────


@pytest.mark.asyncio
@_requires_db
async def test_notification_logged_after_status_update(client: AsyncClient):
    """Full flow: create report, update status, verify notification is logged."""
    import asyncio
    from app.db.supabase import get_supabase_client

    sb = get_supabase_client()
    # Insert report with contact email
    res = await asyncio.to_thread(
        lambda: sb.table("reports").insert({
            "description": "Notification test — flooding on Oak St — safe to delete",
            "latitude": 39.999,
            "longitude": -83.012,
            "status": "submitted",
            "category": "flooding",
            "contact_email": "test-resident@example.com",
        }).execute()
    )
    report_id = res.data[0]["id"]

    try:
        patch_res = await client.patch(
            f"/api/reports/{report_id}/status",
            json={"status": "reviewed", "public_note": "Staff reviewed this."},
        )
        assert patch_res.status_code == 200

        # Give background task a moment to complete
        await asyncio.sleep(0.5)

        # Verify notification was logged
        notif_res = await asyncio.to_thread(
            lambda: sb.table("notifications")
            .select("*")
            .eq("report_id", report_id)
            .execute()
        )
        assert len(notif_res.data) >= 1
        notif = notif_res.data[0]
        assert notif["channel"] == "email"
        assert notif["recipient"] == "test-resident@example.com"
        assert notif["status"] in ("sent", "failed")
    finally:
        await asyncio.to_thread(
            lambda: sb.table("reports").delete().eq("id", report_id).execute()
        )
