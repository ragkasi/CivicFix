"""Database integration tests.

These tests require a real Supabase database with the schema applied.
They are skipped automatically when SUPABASE_URL is not configured.

To run against a real database:
    1. Copy .env.example to backend/.env
    2. Fill in SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL
    3. Apply migrations (001_extensions.sql, 002_schema.sql)
    4. Run: pytest tests/test_db.py -v
"""
import uuid

import pytest
from sqlalchemy import text

from app.config import get_settings
from app.db.session import engine

_settings = get_settings()
_db_configured = bool(_settings.supabase_url and _settings.supabase_service_role_key)

pytestmark = pytest.mark.skipif(
    not _db_configured,
    reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — skipping DB tests",
)


# ─── Connectivity ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_engine_connects():
    """Async engine can reach the database."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


# ─── Extensions ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("ext", ["postgis", "vector", "pgcrypto"])
async def test_extension_installed(ext: str):
    """Required PostgreSQL extensions are present."""
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = :ext"),
            {"ext": ext},
        )
        assert result.scalar() == 1, f"Extension '{ext}' is not installed"


# ─── Schema ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "table",
    [
        "profiles",
        "departments",
        "reports",
        "report_images",
        "ai_analysis",
        "report_embeddings",
        "duplicate_suggestions",
        "status_events",
        "notifications",
    ],
)
async def test_table_exists(table: str):
    """All 9 schema tables are present in the public schema."""
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT 1 FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename = :t"
            ),
            {"t": table},
        )
        assert result.scalar() == 1, f"Table '{table}' not found — run 002_schema.sql"


# ─── Departments ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_departments_table_queryable():
    """departments table can be queried."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT count(*) FROM departments"))
        count = result.scalar()
        assert count is not None
        assert isinstance(count, int)


@pytest.mark.asyncio
async def test_departments_seeded():
    """Exactly 7 departments are present when seed has been applied."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT count(*) FROM departments"))
        count = result.scalar()
    if count == 0:
        pytest.skip("Departments table is empty — run seed_departments.sql first")
    assert count == 7, f"Expected 7 departments, found {count}"


@pytest.mark.asyncio
async def test_departments_have_slugs():
    """All department rows have a non-null slug."""
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT count(*) FROM departments WHERE slug IS NULL OR slug = ''")
        )
        null_count = result.scalar()
    assert null_count == 0, f"{null_count} department(s) are missing a slug"


# ─── PostGIS — geom auto-sync trigger ────────────────────────────────────────


@pytest.mark.asyncio
async def test_postgis_geom_auto_populated():
    """Inserting latitude/longitude auto-populates the geom column via trigger."""
    test_id = str(uuid.uuid4())
    lat, lng = 39.999, -83.012

    async with engine.begin() as conn:
        # Insert test report (geom auto-set by trigger)
        await conn.execute(
            text("""
                INSERT INTO reports (id, description, latitude, longitude)
                VALUES (:id, :desc, :lat, :lng)
            """),
            {"id": test_id, "desc": "Phase 2 PostGIS test — safe to delete", "lat": lat, "lng": lng},
        )

        # Verify geom was set
        result = await conn.execute(
            text("SELECT ST_AsText(geom) FROM reports WHERE id = :id"),
            {"id": test_id},
        )
        geom_text = result.scalar()
        assert geom_text is not None, "geom column was not populated by trigger"
        assert "POINT" in geom_text.upper()

        # Verify coordinates are correct (PostGIS uses lon,lat ordering)
        result = await conn.execute(
            text("""
                SELECT
                  ST_X(geom::geometry) AS lon,
                  ST_Y(geom::geometry) AS lat
                FROM reports WHERE id = :id
            """),
            {"id": test_id},
        )
        row = result.fetchone()
        assert abs(row.lon - lng) < 0.0001
        assert abs(row.lat - lat) < 0.0001

        # Always clean up — DELETE is inside the same transaction
        await conn.execute(text("DELETE FROM reports WHERE id = :id"), {"id": test_id})
    # Transaction commits: INSERT + DELETE both applied, net: no test data remains


@pytest.mark.asyncio
async def test_postgis_radius_query():
    """ST_DWithin can find a report within a given radius."""
    test_id = str(uuid.uuid4())
    lat, lng = 39.999, -83.012

    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO reports (id, description, latitude, longitude) VALUES (:id, :d, :lat, :lng)"),
            {"id": test_id, "d": "Radius test", "lat": lat, "lng": lng},
        )
        result = await conn.execute(
            text("""
                SELECT id FROM reports
                WHERE ST_DWithin(
                    geom,
                    ST_MakePoint(:lng, :lat)::geography,
                    1000
                )
                AND id = :id
            """),
            {"id": test_id, "lat": lat, "lng": lng},
        )
        assert result.fetchone() is not None, "Report not found by radius query"
        await conn.execute(text("DELETE FROM reports WHERE id = :id"), {"id": test_id})


# ─── pgvector — embedding storage and similarity search ───────────────────────


@pytest.mark.asyncio
async def test_pgvector_embedding_insert_and_query():
    """Can insert a vector embedding and run a cosine similarity search."""
    test_report_id = str(uuid.uuid4())

    async with engine.begin() as conn:
        # Insert a minimal report to satisfy FK constraint
        await conn.execute(
            text("INSERT INTO reports (id, description, latitude, longitude) VALUES (:id, :d, :lat, :lng)"),
            {"id": test_report_id, "d": "pgvector test", "lat": 0.0, "lng": 0.0},
        )

        # Insert a dummy 1536-dim embedding (all 0.1)
        await conn.execute(
            text("""
                INSERT INTO report_embeddings (report_id, embedding)
                VALUES (:rid, array_fill(0.1, ARRAY[1536])::vector)
            """),
            {"rid": test_report_id},
        )

        # Cosine similarity query
        result = await conn.execute(
            text("""
                SELECT report_id,
                       embedding <=> array_fill(0.1, ARRAY[1536])::vector AS distance
                FROM report_embeddings
                WHERE report_id = :rid
            """),
            {"rid": test_report_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row.report_id == test_report_id
        # Self-similarity = 0 cosine distance
        assert abs(row.distance) < 0.001, f"Expected ~0 distance, got {row.distance}"

        # Clean up (cascade handles report_embeddings)
        await conn.execute(text("DELETE FROM reports WHERE id = :id"), {"id": test_report_id})
