"""Admin report workflow integration tests.

Require a real Supabase database. Skipped when credentials are not configured.
"""
import asyncio
import uuid

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.schemas.reports import CreateReportRequest, ReportStatus

_settings = get_settings()
_db_configured = bool(_settings.supabase_url and _settings.supabase_service_role_key)

_requires_db = pytest.mark.skipif(
    not _db_configured,
    reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set",
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _create_temp_report() -> tuple[str, str]:
    """Create a test report. Returns (report_id, tracking_token)."""
    from app.services.report_service import ReportService
    service = ReportService()
    resp = await service.create_report(
        CreateReportRequest(
            description="Admin test — pothole on Oak Street near the park",
            latitude=39.999,
            longitude=-83.012,
        )
    )
    return str(resp.id), resp.tracking_token


async def _delete_report(report_id: str) -> None:
    from app.db.supabase import get_supabase_client
    client = get_supabase_client()
    await asyncio.to_thread(
        lambda: client.table("reports").delete().eq("id", report_id).execute()
    )


# ─── Status update ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@_requires_db
async def test_update_status_changes_report_status():
    from app.services.report_service import ReportService
    from app.schemas.reports import UpdateStatusRequest

    report_id, _ = await _create_temp_report()
    service = ReportService()

    try:
        updated = await service.update_status(
            uuid.UUID(report_id),
            UpdateStatusRequest(status=ReportStatus.reviewed, public_note="Report reviewed by staff"),
        )
        assert updated is not None
        assert updated.status == ReportStatus.reviewed
    finally:
        await _delete_report(report_id)


@pytest.mark.asyncio
@_requires_db
async def test_update_status_inserts_status_event():
    from app.db.supabase import get_supabase_client
    from app.services.report_service import ReportService
    from app.schemas.reports import UpdateStatusRequest

    report_id, _ = await _create_temp_report()
    service = ReportService()

    try:
        await service.update_status(
            uuid.UUID(report_id),
            UpdateStatusRequest(
                status=ReportStatus.reviewed,
                public_note="Staff reviewed this report",
            ),
        )

        client = get_supabase_client()
        events = await asyncio.to_thread(
            lambda: client.table("status_events")
            .select("*")
            .eq("report_id", report_id)
            .execute()
        )
        assert len(events.data) >= 1
        latest = events.data[-1]
        assert latest["new_status"] == "reviewed"
        assert latest["old_status"] == "submitted"
        assert latest["public_note"] == "Staff reviewed this report"
    finally:
        await _delete_report(report_id)


@pytest.mark.asyncio
@_requires_db
async def test_update_status_returns_none_for_unknown_report():
    from app.services.report_service import ReportService
    from app.schemas.reports import UpdateStatusRequest

    service = ReportService()
    result = await service.update_status(
        uuid.uuid4(),
        UpdateStatusRequest(status=ReportStatus.reviewed),
    )
    assert result is None


# ─── Department assignment ────────────────────────────────────────────────────

@pytest.mark.asyncio
@_requires_db
async def test_assign_department_updates_department_id():
    from app.db.supabase import get_supabase_client
    from app.services.report_service import ReportService
    from app.schemas.reports import AssignDepartmentRequest

    # Get a real department ID from the seeded data
    client = get_supabase_client()
    dept_result = await asyncio.to_thread(
        lambda: client.table("departments").select("id").limit(1).execute()
    )
    if not dept_result.data:
        pytest.skip("No departments seeded — run seed_departments.py first")

    dept_id = uuid.UUID(dept_result.data[0]["id"])
    report_id, _ = await _create_temp_report()
    service = ReportService()

    try:
        updated = await service.assign_department(
            uuid.UUID(report_id),
            AssignDepartmentRequest(department_id=dept_id),
        )
        assert updated is not None
        assert updated.department_id == dept_id
        assert updated.department is not None
    finally:
        await _delete_report(report_id)


@pytest.mark.asyncio
@_requires_db
async def test_assign_department_raises_for_unknown_department():
    from app.services.report_service import ReportService
    from app.schemas.reports import AssignDepartmentRequest

    report_id, _ = await _create_temp_report()
    service = ReportService()

    try:
        with pytest.raises(ValueError, match="not found"):
            await service.assign_department(
                uuid.UUID(report_id),
                AssignDepartmentRequest(department_id=uuid.uuid4()),
            )
    finally:
        await _delete_report(report_id)


# ─── get_report enriched ─────────────────────────────────────────────────────

@pytest.mark.asyncio
@_requires_db
async def test_get_report_includes_status_events_after_update():
    from app.services.report_service import ReportService
    from app.schemas.reports import UpdateStatusRequest

    report_id, _ = await _create_temp_report()
    service = ReportService()

    try:
        await service.update_status(
            uuid.UUID(report_id),
            UpdateStatusRequest(status=ReportStatus.reviewed),
        )
        detail = await service.get_report(uuid.UUID(report_id))
        assert detail is not None
        assert len(detail.status_events) >= 1
        assert detail.status_events[-1].new_status == "reviewed"
    finally:
        await _delete_report(report_id)


# ─── Departments API ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
@_requires_db
async def test_list_departments_returns_seeded_data():
    from app.services.department_service import DepartmentService

    service = DepartmentService()
    depts = await service.list_departments()

    if len(depts) == 0:
        pytest.skip("No departments seeded — run seed_departments.py first")

    assert len(depts) == 7
    slugs = {d.slug for d in depts}
    assert "public_works" in slugs
    assert "sanitation" in slugs
    assert "transportation" in slugs


@pytest.mark.asyncio
@_requires_db
async def test_api_departments_returns_list(client: AsyncClient):
    response = await client.get("/api/departments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ─── API-level admin tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
@_requires_db
async def test_api_patch_status(client: AsyncClient):
    from app.db.supabase import get_supabase_client

    # Create via API
    payload = {
        "description": "API status update test — broken streetlight on Elm Ave",
        "latitude": 39.990,
        "longitude": -83.000,
    }
    create = await client.post("/api/reports", json=payload)
    assert create.status_code == 201
    report_id = create.json()["id"]

    try:
        patch = await client.patch(
            f"/api/reports/{report_id}/status",
            json={"status": "reviewed", "public_note": "Crew scheduled"},
        )
        assert patch.status_code == 200
        assert patch.json()["status"] == "reviewed"
    finally:
        sb = get_supabase_client()
        await asyncio.to_thread(
            lambda: sb.table("reports").delete().eq("id", report_id).execute()
        )


@pytest.mark.asyncio
@_requires_db
async def test_api_patch_status_404_for_unknown(client: AsyncClient):
    response = await client.patch(
        f"/api/reports/{uuid.uuid4()}/status",
        json={"status": "reviewed"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@_requires_db
async def test_api_patch_department_400_for_unknown_dept(client: AsyncClient):
    from app.db.supabase import get_supabase_client

    payload = {
        "description": "API dept assign test — flooding at Oak and 5th",
        "latitude": 39.980,
        "longitude": -82.990,
    }
    create = await client.post("/api/reports", json=payload)
    assert create.status_code == 201
    report_id = create.json()["id"]

    try:
        patch = await client.patch(
            f"/api/reports/{report_id}/department",
            json={"department_id": str(uuid.uuid4())},
        )
        assert patch.status_code == 400
    finally:
        sb = get_supabase_client()
        await asyncio.to_thread(
            lambda: sb.table("reports").delete().eq("id", report_id).execute()
        )
