"""Report integration tests.

Tests are split into two groups:
- Validation tests (no DB needed) — always run.
- DB integration tests — skip when SUPABASE_URL is not configured.
"""
import asyncio
import io
import uuid

import pytest
from httpx import AsyncClient

from app.config import get_settings

_settings = get_settings()
_db_configured = bool(_settings.supabase_url and _settings.supabase_service_role_key)

_requires_db = pytest.mark.skipif(
    not _db_configured,
    reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — skipping DB tests",
)


# ─── Validation tests — always run (no DB) ────────────────────────────────────


@pytest.mark.asyncio
async def test_api_create_report_rejects_short_description(client: AsyncClient):
    """FastAPI validates description length before the service is called."""
    payload = {"description": "Too short", "latitude": 39.999, "longitude": -83.012}
    response = await client.post("/api/reports", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_create_report_rejects_missing_latitude(client: AsyncClient):
    payload = {"description": "Valid description long enough here", "longitude": -83.012}
    response = await client.post("/api/reports", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_rejects_non_image_content_type(client: AsyncClient):
    fake = io.BytesIO(b"not an image at all")
    response = await client.post(
        "/api/upload/image",
        files={"file": ("data.txt", fake, "text/plain")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_rejects_oversized_file(client: AsyncClient):
    big = io.BytesIO(b"x" * (11 * 1024 * 1024))  # 11 MB
    response = await client.post(
        "/api/upload/image",
        files={"file": ("big.jpg", big, "image/jpeg")},
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_valid_image_without_storage_returns_503_not_500(
    client: AsyncClient,
):
    """Without storage credentials the route must return 503, never 500."""
    if _settings.supabase_url and _settings.supabase_storage_bucket:
        pytest.skip("Storage configured — 503 path not reachable")
    tiny = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
    response = await client.post(
        "/api/upload/image",
        files={"file": ("photo.jpg", tiny, "image/jpeg")},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_api_tracking_unknown_token_returns_404_or_503(client: AsyncClient):
    """Unknown token returns 404 (DB up) or 503 (no credentials) — never 500."""
    response = await client.get("/api/tracking/completely-fake-token-xyz-0000")
    assert response.status_code in (404, 503)


# ─── DB integration tests — skip without credentials ─────────────────────────


@pytest.mark.asyncio
@_requires_db
async def test_create_report_returns_tracking_token():
    from app.db.supabase import get_supabase_client
    from app.schemas.reports import CreateReportRequest, ReportStatus
    from app.services.report_service import ReportService

    service = ReportService()
    req = CreateReportRequest(
        description="Test pothole near the library entrance — Phase 3 test",
        latitude=39.999,
        longitude=-83.012,
        address="123 Test St",
    )
    response = await service.create_report(req)
    report_id = str(response.id)

    try:
        assert response.id is not None
        assert response.status == ReportStatus.submitted
        assert response.tracking_token is not None
        assert len(response.tracking_token) >= 10
        assert response.created_at is not None
    finally:
        client = get_supabase_client()
        await asyncio.to_thread(
            lambda: client.table("reports").delete().eq("id", report_id).execute()
        )


@pytest.mark.asyncio
@_requires_db
async def test_tracking_returns_safe_fields_only():
    from app.db.supabase import get_supabase_client
    from app.schemas.reports import CreateReportRequest
    from app.services.report_service import ReportService

    service = ReportService()
    req = CreateReportRequest(
        description="Flooding near bus stop after rain — Phase 3 tracking test",
        latitude=39.998,
        longitude=-83.011,
        contact_email="private@example.com",
        contact_phone="+15550001234",
    )
    response = await service.create_report(req)
    report_id = str(response.id)

    try:
        tracking = await service.get_report_by_tracking_token(response.tracking_token)
        assert tracking is not None
        assert tracking.status == "submitted"
        assert tracking.tracking_token == response.tracking_token

        # Private fields must not appear in tracking response
        data = tracking.model_dump()
        assert "contact_email" not in data or data.get("contact_email") is None
        assert "contact_phone" not in data or data.get("contact_phone") is None
    finally:
        client = get_supabase_client()
        await asyncio.to_thread(
            lambda: client.table("reports").delete().eq("id", report_id).execute()
        )


@pytest.mark.asyncio
@_requires_db
async def test_tracking_returns_none_for_unknown_token():
    from app.services.report_service import ReportService

    service = ReportService()
    result = await service.get_report_by_tracking_token("nonexistent-0000000000")
    assert result is None


@pytest.mark.asyncio
@_requires_db
async def test_list_reports_returns_list():
    from app.services.report_service import ReportService

    service = ReportService()
    result = await service.list_reports(limit=5)
    assert isinstance(result, list)


@pytest.mark.asyncio
@_requires_db
async def test_get_report_returns_none_for_unknown_id():
    from app.services.report_service import ReportService

    service = ReportService()
    result = await service.get_report(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
@_requires_db
async def test_api_full_submit_and_track_flow(client: AsyncClient):
    """End-to-end: submit → tracking token → tracking page."""
    from app.db.supabase import get_supabase_client

    payload = {
        "description": "Graffiti on the underpass wall near Oak and 5th — E2E test",
        "latitude": 39.995,
        "longitude": -83.009,
        "address": "Oak St & 5th Ave",
    }
    create_res = await client.post("/api/reports", json=payload)
    assert create_res.status_code == 201
    body = create_res.json()
    token = body["tracking_token"]
    report_id = body["id"]

    try:
        track_res = await client.get(f"/api/tracking/{token}")
        assert track_res.status_code == 200
        track = track_res.json()
        assert track["status"] == "submitted"
        assert track["tracking_token"] == token
        assert "contact_email" not in track
        assert "contact_phone" not in track
    finally:
        sb = get_supabase_client()
        await asyncio.to_thread(
            lambda: sb.table("reports").delete().eq("id", report_id).execute()
        )
