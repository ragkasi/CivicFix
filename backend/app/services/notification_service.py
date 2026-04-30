"""Resident notification service — email and SMS on status changes."""
import asyncio
import base64
import logging

import httpx

from app.config import get_settings
from app.db.supabase import get_supabase_client
from app.schemas.notifications import NotificationResult

logger = logging.getLogger(__name__)


def _run(fn):
    return asyncio.to_thread(fn)


# ─── Message builder (pure — easy to test) ───────────────────────────────────

_STATUS_MESSAGES: dict[str, str] = {
    "reviewed":    "Your report has been reviewed by city staff.",
    "assigned":    "Your report has been assigned to a city department.",
    "in_progress": "A city crew is actively working on your report.",
    "resolved":    "Great news — your report has been resolved. Thank you for helping improve our city.",
    "rejected":    "Your report has been reviewed and could not be actioned at this time.",
    "duplicate":   "Your report has been marked as a duplicate of an existing open report.",
}


def build_resident_message(status: str, public_note: str | None = None) -> str:
    """Build a resident-facing notification message for a status change.

    Pure function — no I/O. Used by tests and the service.
    """
    base = _STATUS_MESSAGES.get(
        status, f"Your report status has been updated to: {status.replace('_', ' ')}."
    )
    if public_note:
        return f"{base}\n\nMessage from city staff: {public_note}"
    return base


def build_subject(status: str) -> str:
    label = status.replace("_", " ").title()
    return f"CivicFix — Report Update: {label}"


# ─── Service ──────────────────────────────────────────────────────────────────


class NotificationService:
    def _client(self):
        return get_supabase_client()

    async def send_status_update(
        self,
        report_id: str,
        new_status: str | None = None,
        public_note: str | None = None,
    ) -> list[NotificationResult]:
        """Send status-change notifications to the resident.

        If new_status is None, fetches current status from the database.
        Returns empty list when the report has no contact info.
        Designed to be called as a FastAPI BackgroundTask — logs errors, never raises.
        """
        settings = get_settings()
        try:
            client = self._client()
        except RuntimeError:
            logger.warning("Notification skipped — Supabase not configured")
            return []

        # Fetch report contact info and current status
        res = await _run(
            lambda: client.table("reports")
            .select("id, status, contact_email, contact_phone")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            return []

        row = res.data[0]
        status = new_status or row["status"]
        contact_email = row.get("contact_email")
        contact_phone = row.get("contact_phone")

        if not contact_email and not contact_phone:
            logger.info(f"report {report_id}: no contact info — skipping notification")
            return [NotificationResult(channel="email", recipient="none", status="skipped")]

        message = build_resident_message(status, public_note)
        subject = build_subject(status)
        results: list[NotificationResult] = []

        if contact_email:
            r = await self._send_email(client, report_id, contact_email, subject, message, settings)
            results.append(r)

        if contact_phone:
            r = await self._send_sms(client, report_id, contact_phone, message, settings)
            results.append(r)

        return results

    # ─── Private senders ──────────────────────────────────────────────────────

    async def _send_email(self, client, report_id, email, subject, body, settings) -> NotificationResult:
        provider = (settings.email_provider or "").lower()

        if provider == "resend" and settings.email_api_key:
            return await self._send_resend(client, report_id, email, subject, body, settings)
        elif provider == "sendgrid" and settings.email_api_key:
            return await self._send_sendgrid(client, report_id, email, subject, body, settings)
        else:
            # Mock — log the send without calling an external provider
            logger.info(f"[MOCK] Email → {email[:3]}***{email.split('@')[-1]}: {subject}")
            await self._log(client, report_id, "email", email, subject, body, "sent", {"mock": True, "provider": provider or "none"})
            return NotificationResult(channel="email", recipient=email, status="sent", is_mock=True)

    async def _send_resend(self, client, report_id, email, subject, body, settings) -> NotificationResult:
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.email_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"from": settings.email_from, "to": [email], "subject": subject, "text": body},
                )
                resp.raise_for_status()
                provider_response = resp.json()
                status = "sent"
                error = None
        except Exception as exc:
            logger.error(f"Resend email failed: {exc}")
            provider_response = {"error": str(exc)}
            status = "failed"
            error = str(exc)

        await self._log(client, report_id, "email", email, subject, body, status, provider_response)
        return NotificationResult(channel="email", recipient=email, status=status, error=error)

    async def _send_sendgrid(self, client, report_id, email, subject, body, settings) -> NotificationResult:
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {settings.email_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [{"to": [{"email": email}]}],
                        "from": {"email": settings.email_from},
                        "subject": subject,
                        "content": [{"type": "text/plain", "value": body}],
                    },
                )
                resp.raise_for_status()
                provider_response = {"status_code": resp.status_code}
                status = "sent"
                error = None
        except Exception as exc:
            logger.error(f"SendGrid email failed: {exc}")
            provider_response = {"error": str(exc)}
            status = "failed"
            error = str(exc)

        await self._log(client, report_id, "email", email, subject, body, status, provider_response)
        return NotificationResult(channel="email", recipient=email, status=status, error=error)

    async def _send_sms(self, client, report_id, phone, body, settings) -> NotificationResult:
        if settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number:
            return await self._send_twilio(client, report_id, phone, body, settings)

        logger.info(f"[MOCK] SMS → {phone[:4]}***: {body[:40]}")
        await self._log(client, report_id, "sms", phone, None, body, "sent", {"mock": True})
        return NotificationResult(channel="sms", recipient=phone, status="sent", is_mock=True)

    async def _send_twilio(self, client, report_id, phone, body, settings) -> NotificationResult:
        try:
            auth = base64.b64encode(
                f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode()
            ).decode()
            url = (
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{settings.twilio_account_sid}/Messages.json"
            )
            async with httpx.AsyncClient(timeout=10.0) as http:
                resp = await http.post(
                    url,
                    data={"From": settings.twilio_phone_number, "To": phone, "Body": body},
                    headers={"Authorization": f"Basic {auth}"},
                )
                resp.raise_for_status()
                provider_response = resp.json()
                status = "sent"
                error = None
        except Exception as exc:
            logger.error(f"Twilio SMS failed: {exc}")
            provider_response = {"error": str(exc)}
            status = "failed"
            error = str(exc)

        await self._log(client, report_id, "sms", phone, None, body, status, provider_response)
        return NotificationResult(channel="sms", recipient=phone, status=status, error=error)

    async def _log(self, client, report_id, channel, recipient, subject, body, status, provider_response) -> None:
        row: dict = {
            "report_id": report_id,
            "channel": channel,
            "recipient": recipient,
            "body": body,
            "status": status,
            "provider_response": provider_response,
        }
        if subject:
            row["subject"] = subject
        if status == "sent":
            from datetime import datetime, timezone
            row["sent_at"] = datetime.now(tz=timezone.utc).isoformat()
        try:
            await _run(lambda: client.table("notifications").insert(row).execute())
        except Exception as exc:
            logger.warning(f"Could not log notification: {exc}")
