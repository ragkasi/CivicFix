# CivicFix — Backend

FastAPI service for the CivicFix civic issue reporting platform.

## Tech Stack

- Python 3.12, FastAPI, uvicorn
- Pydantic v2 (schemas and settings)
- SQLAlchemy 2 (async) + asyncpg
- Supabase Python client (Storage, PostgREST)
- pytest + pytest-asyncio

## Getting Started

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env — fill in DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# Start dev server
uvicorn app.main:app --reload
```

Server: **http://localhost:8000**
Swagger: **http://localhost:8000/docs**
Health: **GET /health**

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase Postgres connection string (`postgresql+asyncpg://...`) |
| `SUPABASE_URL` | Supabase project URL (`https://xxx.supabase.co`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (bypasses RLS — keep private) |
| `SUPABASE_ANON_KEY` | Anon/public key |
| `SUPABASE_STORAGE_BUCKET` | Storage bucket name (default: `report-images`) |
| `OPENAI_API_KEY` | OpenAI key (placeholder — wired in Phase 4) |

See `.env.example` at the repo root for the full list.

## Running Tests

```bash
cd backend

# All tests (health tests pass; DB tests skip without credentials)
pytest

# Verbose output
pytest -v

# Only DB tests (requires real Supabase credentials in .env)
pytest tests/test_db.py -v
```

DB tests skip automatically when `SUPABASE_URL` is not configured. This is
intentional — CI does not require a live database in Phase 1-2.

## Database Scripts

These scripts require `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`.

### Check database connectivity and schema

```bash
cd backend
python scripts/check_database.py
```

Exits 0 on success, 1 on failure. Useful for verifying a Supabase project
is correctly set up before running the app.

### Seed departments

```bash
cd backend
python scripts/seed_departments.py
```

Upserts the 7 initial city departments. Safe to run multiple times.

## Project Structure

```
app/
  main.py          FastAPI app factory, CORS, health check
  config.py        Settings via pydantic-settings + .env
  api/             Route handlers (thin — delegate to services)
  services/        Business logic (Phase 3+)
  schemas/         Pydantic request/response models
  models/          SQLAlchemy ORM models (Phase 3+)
  db/
    session.py     Async SQLAlchemy engine + get_db dependency
    supabase.py    Supabase Python client (Storage operations)
  ai/              Prompt helpers, vision, embeddings (Phase 4+)
scripts/
  check_database.py  DB connectivity and schema check
  seed_departments.py  Seed city departments
tests/
  test_health.py   Health endpoint tests (always run)
  test_db.py       DB integration tests (skip without credentials)
```
