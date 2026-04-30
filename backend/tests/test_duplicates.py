"""Duplicate detection tests.

Pure scoring tests run without any external dependencies.
DB-dependent tests skip when SUPABASE_URL is not configured.
"""
import uuid

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.services.duplicate_service import build_reason, calculate_combined_score

_settings = get_settings()
_db_configured = bool(_settings.supabase_url and _settings.supabase_service_role_key)
_requires_db = pytest.mark.skipif(
    not _db_configured,
    reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set",
)


# ─── calculate_combined_score — pure function ──────────────────────────────────


def test_combined_score_all_perfect():
    score = calculate_combined_score(
        semantic_score=1.0,
        distance_meters=0.0,
        radius_meters=500.0,
        candidate_age_days=0,
    )
    assert score == pytest.approx(1.0)


def test_combined_score_all_zero():
    score = calculate_combined_score(
        semantic_score=0.0,
        distance_meters=500.0,
        radius_meters=500.0,
        candidate_age_days=30,
    )
    assert score == pytest.approx(0.0)


def test_location_score_higher_for_closer_reports():
    close = calculate_combined_score(0.7, 50.0, 500.0, 5)
    far = calculate_combined_score(0.7, 400.0, 500.0, 5)
    assert close > far


def test_recency_score_higher_for_newer_reports():
    new = calculate_combined_score(0.7, 100.0, 500.0, 1)
    old = calculate_combined_score(0.7, 100.0, 500.0, 25)
    assert new > old


def test_combined_score_between_0_and_1():
    for sem in [0.0, 0.5, 1.0]:
        for dist in [0, 250, 500]:
            for age in [0, 15, 30]:
                score = calculate_combined_score(sem, dist, 500.0, age)
                assert 0.0 <= score <= 1.0, f"Out of range: {score}"


def test_combined_score_weights():
    # semantic=1, location=0, recency=0 → 0.60
    s = calculate_combined_score(1.0, 500.0, 500.0, 30)
    assert s == pytest.approx(0.60)

    # semantic=0, location=1, recency=0 → 0.25
    s = calculate_combined_score(0.0, 0.0, 500.0, 30)
    assert s == pytest.approx(0.25)

    # semantic=0, location=0, recency=1 → 0.15
    s = calculate_combined_score(0.0, 500.0, 500.0, 0)
    assert s == pytest.approx(0.15)


def test_distance_beyond_radius_clamps_to_zero():
    score = calculate_combined_score(0.5, 1000.0, 500.0, 5)
    # location_score clamps at 0, should not be negative
    assert score >= 0.0


# ─── build_reason — pure function ─────────────────────────────────────────────


def test_build_reason_high_similarity():
    r = build_reason(0.85, 300.0)
    assert "very similar" in r


def test_build_reason_close_distance():
    r = build_reason(0.5, 30.0)
    assert "same location" in r


def test_build_reason_nearby():
    r = build_reason(0.5, 300.0)
    assert "nearby" in r


def test_build_reason_fallback():
    r = build_reason(0.1, 600.0)
    assert r  # must return something


# ─── API validation — always run ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duplicates_endpoint_rejects_oversized_radius(client: AsyncClient):
    res = await client.post(
        f"/api/reports/{uuid.uuid4()}/duplicates?radius_meters=99999"
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_duplicates_endpoint_rejects_oversized_limit(client: AsyncClient):
    res = await client.post(
        f"/api/reports/{uuid.uuid4()}/duplicates?limit=999"
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_duplicates_endpoint_unknown_report_no_500(client: AsyncClient):
    """For an unknown report, the endpoint must return 200 [] or 503 — never 500."""
    res = await client.post(
        f"/api/reports/{uuid.uuid4()}/duplicates"
    )
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        assert res.json() == []


# ─── DB integration — skip without credentials ────────────────────────────────


@pytest.mark.asyncio
@_requires_db
async def test_find_duplicates_returns_list_for_report_without_embedding(
    client: AsyncClient,
):
    """A report with no embedding returns an empty list, not an error."""
    from app.db.supabase import get_supabase_client
    import asyncio

    sb = get_supabase_client()

    # Insert a minimal report (no embedding)
    result = await asyncio.to_thread(
        lambda: sb.table("reports").insert({
            "description": "Duplicate test report — no embedding — safe to delete",
            "latitude": 39.999,
            "longitude": -83.012,
            "status": "submitted",
            "category": "other",
        }).execute()
    )
    report_id = result.data[0]["id"]

    try:
        res = await client.post(f"/api/reports/{report_id}/duplicates")
        assert res.status_code == 200
        assert res.json() == []  # No embedding → RPC returns nothing
    finally:
        await asyncio.to_thread(
            lambda: sb.table("reports").delete().eq("id", report_id).execute()
        )


@pytest.mark.asyncio
@_requires_db
async def test_find_duplicates_excludes_source_report(client: AsyncClient):
    """Duplicate detection must never return the source report as its own duplicate."""
    from app.db.supabase import get_supabase_client
    import asyncio

    sb = get_supabase_client()
    result = await asyncio.to_thread(
        lambda: sb.table("reports").insert({
            "description": "Duplicate exclusion test — safe to delete",
            "latitude": 39.999,
            "longitude": -83.012,
            "status": "submitted",
            "category": "other",
        }).execute()
    )
    report_id = result.data[0]["id"]

    try:
        res = await client.post(f"/api/reports/{report_id}/duplicates")
        assert res.status_code == 200
        for candidate in res.json():
            assert candidate["candidate_report_id"] != report_id
    finally:
        await asyncio.to_thread(
            lambda: sb.table("reports").delete().eq("id", report_id).execute()
        )
