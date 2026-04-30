"""Geospatial endpoint tests.

- Always-run tests: bbox parsing validation, route ordering.
- DB-dependent tests: nearby endpoint, bbox filtering.
  These skip when SUPABASE_URL is not configured.
"""
import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.services.report_service import _parse_bbox

_settings = get_settings()
_db_configured = bool(_settings.supabase_url and _settings.supabase_service_role_key)
_requires_db = pytest.mark.skipif(
    not _db_configured,
    reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set",
)


# ─── bbox parsing — always run ────────────────────────────────────────────────


def test_parse_bbox_valid():
    min_lng, min_lat, max_lng, max_lat = _parse_bbox("-83.05,39.98,-82.95,40.02")
    assert min_lng == pytest.approx(-83.05)
    assert min_lat == pytest.approx(39.98)
    assert max_lng == pytest.approx(-82.95)
    assert max_lat == pytest.approx(40.02)


def test_parse_bbox_too_few_parts():
    with pytest.raises(ValueError, match="4 comma-separated"):
        _parse_bbox("-83.05,39.98,-82.95")


def test_parse_bbox_non_numeric():
    with pytest.raises(ValueError, match="numeric"):
        _parse_bbox("-83.05,39.98,-82.95,abc")


def test_parse_bbox_longitude_out_of_range():
    with pytest.raises(ValueError, match="[Ll]ongitude"):
        _parse_bbox("190,39.98,-82.95,40.02")


def test_parse_bbox_latitude_out_of_range():
    with pytest.raises(ValueError, match="[Ll]atitude"):
        _parse_bbox("-83.05,95,-82.95,40.02")


# ─── API validation — always run ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_nearby_rejects_missing_lat(client: AsyncClient):
    """Missing required lat parameter → 422."""
    res = await client.get("/api/reports/nearby?lng=-83.0")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_api_nearby_rejects_missing_lng(client: AsyncClient):
    res = await client.get("/api/reports/nearby?lat=40.0")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_api_nearby_rejects_invalid_lat(client: AsyncClient):
    res = await client.get("/api/reports/nearby?lat=200&lng=-83.0")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_api_nearby_rejects_oversized_radius(client: AsyncClient):
    res = await client.get("/api/reports/nearby?lat=40.0&lng=-83.0&radius_km=999")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_api_list_rejects_invalid_bbox(client: AsyncClient):
    """Invalid bbox format → 400."""
    res = await client.get("/api/reports?bbox=bad,format")
    assert res.status_code in (400, 503)  # 400 if parsed; 503 if db hit first


@pytest.mark.asyncio
async def test_nearby_route_is_not_swallowed_by_report_id(client: AsyncClient):
    """/api/reports/nearby must not be routed to GET /api/reports/{report_id}.

    The route should return 422 (missing params) or 503 (no DB) — not 422 from
    UUID parsing of the literal string 'nearby'.
    """
    res = await client.get("/api/reports/nearby")
    # Without lat/lng it should be 422 (FastAPI query param validation),
    # NOT 422 from UUID parsing or 404.
    assert res.status_code == 422
    detail = res.json()
    # Should complain about missing 'lat', not about invalid UUID
    body_str = str(detail)
    assert "nearby" not in body_str.lower() or "lat" in body_str.lower()


# ─── DB integration — skip without credentials ────────────────────────────────


@pytest.mark.asyncio
@_requires_db
async def test_api_nearby_returns_list(client: AsyncClient):
    """Nearby endpoint returns a list (possibly empty) for valid coords."""
    res = await client.get("/api/reports/nearby?lat=39.999&lng=-83.012&radius_km=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
@_requires_db
async def test_api_nearby_includes_distance_meters(client: AsyncClient):
    """Each nearby result has distance_meters field."""
    res = await client.get("/api/reports/nearby?lat=39.999&lng=-83.012&radius_km=50")
    assert res.status_code == 200
    results = res.json()
    for r in results:
        assert "distance_meters" in r
        assert r["distance_meters"] >= 0


@pytest.mark.asyncio
@_requires_db
async def test_api_list_with_bbox_returns_list(client: AsyncClient):
    """List endpoint with valid bbox returns a list."""
    res = await client.get("/api/reports?bbox=-84.0,39.0,-82.0,41.0&limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
