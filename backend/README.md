# CivicFix — Backend

FastAPI service for the CivicFix civic issue reporting platform.

## Tech Stack

- Python 3.12, FastAPI, uvicorn
- Pydantic v2 (schemas and settings)
- SQLAlchemy 2 async + asyncpg (complex DB queries)
- Supabase Python client (CRUD + Storage)
- python-multipart (file upload)
- pytest + pytest-asyncio

## Getting Started

```bash
cd backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example .env
# Fill in DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

uvicorn app.main:app --reload
```

Server: **http://localhost:8000**
Swagger: **http://localhost:8000/docs**

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` Supabase direct connection |
| `SUPABASE_URL` | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (bypasses RLS) |
| `SUPABASE_ANON_KEY` | Anon/public key |
| `SUPABASE_STORAGE_BUCKET` | Storage bucket name (default: `report-images`) |
| `OPENAI_API_KEY` | OpenAI key (placeholder — Phase 4) |

## API Endpoints (Phase 3)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/reports` | Submit a new report |
| `GET` | `/api/reports` | List reports (with filters) |
| `GET` | `/api/reports/{id}` | Get report detail |
| `PATCH` | `/api/reports/{id}/status` | Update status (Phase 4) |
| `PATCH` | `/api/reports/{id}/department` | Assign department (Phase 4) |
| `GET` | `/api/tracking/{token}` | Public resident tracking |
| `POST` | `/api/upload/image` | Upload report image |
| `GET` | `/api/departments` | List departments |

## Running Tests

```bash
# All tests (validation tests run; DB tests skip without credentials)
pytest

# Verbose
pytest -v

# DB tests (requires real Supabase credentials in .env)
pytest tests/test_db.py tests/test_reports.py -v -k "db or tracking or create"
```

Tests are split:
- **Validation tests** — always run, no DB needed (upload rejections, schema validation)
- **DB integration tests** — skip when `SUPABASE_URL` is unset

## Database Scripts

```bash
cd backend

# Check DB connectivity and schema
python scripts/check_database.py

# Seed departments (idempotent)
python scripts/seed_departments.py
```

## Project Structure

```
app/
  main.py           FastAPI app + CORS + router registration
  config.py         pydantic-settings Settings class
  api/
    reports.py      Report CRUD routes
    departments.py  Department list route
    tracking.py     Public tracking route
    upload.py       Image upload route
  services/
    report_service.py    create_report, list_reports, get_report,
                         get_report_by_tracking_token (Phase 3)
    department_service.py  list_departments stub (Phase 3)
  schemas/
    reports.py      Enums + request/response models
    departments.py  DepartmentResponse
    tracking.py     TrackingResponse
  db/
    session.py      Async SQLAlchemy engine + get_db
    supabase.py     Supabase client + upload_report_image
  ai/               Prompts, vision, embeddings (Phase 4)
  models/           SQLAlchemy ORM models (Phase 4)
scripts/
  check_database.py   DB connectivity check
  seed_departments.py Seed 7 city departments
tests/
  test_health.py    Health endpoint (always run)
  test_db.py        DB schema tests (skip without credentials)
  test_reports.py   Report + upload tests (split: some always run)
```
