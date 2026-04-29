#!/usr/bin/env python
"""Seed the departments table via the Supabase Python client.

Run from inside the backend/ directory:
    python scripts/seed_departments.py

Safe to run multiple times — uses upsert on slug to avoid duplicates.
"""
import sys
import os

# Allow imports from the backend root when running as a standalone script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.supabase import get_supabase_client

DEPARTMENTS = [
    {
        "slug": "public_works",
        "name": "Public Works",
        "description": "Handles road infrastructure, sidewalks, and drainage systems.",
        "category_coverage": ["pothole", "road_hazard", "sidewalk_damage", "flooding", "snow_or_ice"],
        "contact_email": "publicworks@city.gov",
    },
    {
        "slug": "transportation",
        "name": "Transportation",
        "description": "Manages traffic signals, road signs, and street safety.",
        "category_coverage": ["damaged_sign", "streetlight"],
        "contact_email": "transportation@city.gov",
    },
    {
        "slug": "sanitation",
        "name": "Sanitation",
        "description": "Manages trash collection, overflow cleanup, and graffiti removal.",
        "category_coverage": ["trash_overflow", "graffiti"],
        "contact_email": "sanitation@city.gov",
    },
    {
        "slug": "parks_and_recreation",
        "name": "Parks and Recreation",
        "description": "Maintains public parks, trails, and urban trees.",
        "category_coverage": ["other"],
        "contact_email": "parks@city.gov",
    },
    {
        "slug": "water_and_drainage",
        "name": "Water and Drainage",
        "description": "Manages water mains, storm drains, and flood response.",
        "category_coverage": ["flooding"],
        "contact_email": "water@city.gov",
    },
    {
        "slug": "code_enforcement",
        "name": "Code Enforcement",
        "description": "Handles zoning violations, blight, and public nuisance issues.",
        "category_coverage": ["graffiti", "other"],
        "contact_email": "codeenforcement@city.gov",
    },
    {
        "slug": "general_services",
        "name": "General Services",
        "description": "Handles miscellaneous city operations not covered by other departments.",
        "category_coverage": ["other"],
        "contact_email": "generalservices@city.gov",
    },
]


def main() -> None:
    try:
        client = get_supabase_client()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Seeding {len(DEPARTMENTS)} departments...")

    for dept in DEPARTMENTS:
        result = (
            client.table("departments")
            .upsert(dept, on_conflict="slug")
            .execute()
        )
        if result.data:
            print(f"  ✓ {dept['name']} ({dept['slug']})")
        else:
            print(f"  ~ {dept['name']} already exists (no change)")

    # Verify final count
    count_result = client.table("departments").select("id", count="exact").execute()
    total = count_result.count if count_result.count is not None else "unknown"
    print(f"\nDone. Total departments in database: {total}")


if __name__ == "__main__":
    main()
