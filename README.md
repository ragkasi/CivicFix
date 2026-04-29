# CivicFix

AI-powered civic issue reporting and routing platform. Residents submit local infrastructure issues with photos, descriptions, and map locations. AI classifies the issue, estimates severity, detects duplicates, and routes the report to the correct city department.

## Current Phase: Phase 2 — Supabase Database Foundation

Backend and frontend foundations are in place. The database schema is defined and validated. Full business logic and AI features are built in Phases 3–6.

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Supabase project (free tier works for development)

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Copy the **Project URL** and **API keys** from Settings → API
3. Copy the **Database connection string** from Settings → Database (use the direct connection URL, not the pooler, for local development)

### 2. Apply Database Migrations

In the Supabase **SQL Editor**, run these files in order:

```
supabase/migrations/001_extensions.sql   -- postgis, vector, pgcrypto
supabase/migrations/002_schema.sql       -- all 9 tables + indexes + trigger
supabase/seed/seed_departments.sql       -- 7 city departments
```

Each file is idempotent and safe to re-run.

### 3. Configure Environment Variables

```bash
# Backend
cd backend
cp ../.env.example .env
# Edit backend/.env — fill in:
#   DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[pass]@aws-...supabase.com:5432/postgres
#   SUPABASE_URL=https://xxx.supabase.co
#   SUPABASE_SERVICE_ROLE_KEY=eyJ...
#   SUPABASE_ANON_KEY=eyJ...

# Frontend
cd frontend
cp ../.env.example .env.local
# Edit frontend/.env.local — fill in:
#   NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
#   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
#   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 4. Run the Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: **http://localhost:8000**
Swagger: **http://localhost:8000/docs**

### 5. Verify Database Setup

```bash
cd backend
python scripts/check_database.py
```

Expected output when fully configured:

```
CivicFix - Database Check
----------------------------------------
  [PASS] Database connection
  [PASS] Extension: postgis
  [PASS] Extension: vector
  [PASS] Extension: pgcrypto
  [PASS] Table: profiles
  ... (all 9 tables)
  [PASS] Departments: 7 (fully seeded)

Result: All checks passed.
```

### 6. Seed Departments (alternative to SQL file)

```bash
cd backend
python scripts/seed_departments.py
```

This upserts the 7 initial departments via the Supabase Python client. Safe to run multiple times.

### 7. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: **http://localhost:3000**

### 8. Run Tests

```bash
cd backend
pytest                     # health tests pass; DB tests skip without credentials
pytest tests/test_db.py -v # DB tests — require real Supabase credentials
```

## Project Structure

```
frontend/          Next.js resident and admin UI
backend/           FastAPI backend API
  scripts/         Database check and seed scripts
mcp-server/        city-ops-mcp MCP server (Phase 7)
supabase/
  migrations/      001_extensions.sql, 002_schema.sql
  seed/            seed_departments.sql
docs/              Supporting documentation
.claude/           Claude agents, skills, commands, hooks
```

## Documentation

| Doc | Description |
|-----|-------------|
| [CLAUDE.md](CLAUDE.md) | Project guide for Claude |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture |
| [API_CONTRACT.md](API_CONTRACT.md) | API endpoint contracts |
| [DATA_MODEL.md](DATA_MODEL.md) | Database schema |
| [AI_PIPELINE.md](AI_PIPELINE.md) | AI classification pipeline |
| [MCP_DESIGN.md](MCP_DESIGN.md) | MCP server design |
| [FRONTEND_SPEC.md](FRONTEND_SPEC.md) | Frontend pages and components |
| [BACKEND_SPEC.md](BACKEND_SPEC.md) | Backend structure and services |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Phase-by-phase plan |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Demo walkthrough |

## Database Schema (Phase 2)

9 tables defined in `supabase/migrations/002_schema.sql`:

| Table | Purpose |
|-------|---------|
| `profiles` | Resident and admin user metadata (extends Supabase auth) |
| `departments` | City departments with slug, name, and category coverage |
| `reports` | Civic issue reports with PostGIS geom + public_tracking_token |
| `report_images` | Uploaded images (extensible — MVP shows one, table supports many) |
| `ai_analysis` | AI classification outputs per report (Phase 4) |
| `report_embeddings` | vector(1536) embeddings for duplicate detection (Phase 5) |
| `duplicate_suggestions` | Candidate duplicate pairs for admin review (Phase 5) |
| `status_events` | Append-only status transition audit log |
| `notifications` | Outbound email/SMS notification log (Phase 6) |

Key schema decisions:
- Severity: `low / medium / high / critical` (string)
- Status: `submitted / reviewed / assigned / in_progress / resolved / duplicate / rejected` (string)
- Category: API slugs (`pothole`, `flooding`, `graffiti`, etc.)
- `reports.geom` is auto-synced from `latitude`/`longitude` via a Postgres trigger
- `report_embeddings.embedding` uses `vector(1536)` matching `text-embedding-3-small`
- `departments.slug` is unique and used as the conflict-safe seed target
