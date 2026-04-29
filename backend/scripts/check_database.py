#!/usr/bin/env python
"""Quick database connectivity and schema sanity check.

Run from inside the backend/ directory:
    python scripts/check_database.py

Exits with code 0 on success, 1 on failure.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.config import get_settings
from app.db.session import engine


def ok(msg: str) -> None:
    print(f"  [PASS] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def info(msg: str) -> None:
    print(f"  [INFO] {msg}")


async def check() -> bool:
    settings = get_settings()
    passed = True

    print("CivicFix - Database Check")
    print("-" * 40)
    db_url_display = settings.database_url[:50] + "..." if len(settings.database_url) > 50 else settings.database_url
    print(f"DATABASE_URL : {db_url_display}")
    print(f"SUPABASE_URL : {settings.supabase_url or '(not set)'}")
    print()

    try:
        async with engine.connect() as conn:
            # Basic connectivity
            await conn.execute(text("SELECT 1"))
            ok("Database connection")

            # Check extensions
            for ext in ("postgis", "vector", "pgcrypto"):
                result = await conn.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = :ext"),
                    {"ext": ext},
                )
                if result.scalar():
                    ok(f"Extension: {ext}")
                else:
                    fail(f"Extension: {ext} -- run 001_extensions.sql")
                    passed = False

            # Check tables
            expected_tables = [
                "profiles", "departments", "reports", "report_images",
                "ai_analysis", "report_embeddings", "duplicate_suggestions",
                "status_events", "notifications",
            ]
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            existing = {row[0] for row in result.fetchall()}
            for table in expected_tables:
                if table in existing:
                    ok(f"Table: {table}")
                else:
                    fail(f"Table: {table} -- run 002_schema.sql")
                    passed = False

            # Department count
            if "departments" in existing:
                result = await conn.execute(text("SELECT count(*) FROM departments"))
                count = result.scalar()
                if count == 7:
                    ok(f"Departments: {count} (fully seeded)")
                elif count and count > 0:
                    info(f"Departments: {count} (partially seeded, expected 7)")
                else:
                    info("Departments: 0 -- run seed_departments.sql or scripts/seed_departments.py")

    except Exception as e:
        fail(f"Database connection FAILED: {e}")
        passed = False

    print()
    if passed:
        print("Result: All checks passed.")
    else:
        print("Result: Some checks failed -- see above.")

    return passed


def main() -> None:
    ok_result = asyncio.run(check())
    sys.exit(0 if ok_result else 1)


if __name__ == "__main__":
    main()
