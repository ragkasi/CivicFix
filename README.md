# CivicFix

AI-powered civic issue reporting and routing platform. Residents submit local infrastructure issues with photos, descriptions, and map locations. AI classifies the issue, estimates severity, detects duplicates, and routes the report to the correct city department.

## Current Phase: Phase 3 — Resident Report Submission MVP

Residents can submit reports and track them via a public token. The backend stores reports in Supabase, handles image uploads to Supabase Storage, and returns tracking tokens. AI features, the admin dashboard, and realtime updates are built in Phases 4–6.

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Supabase project with migrations applied (see Phase 2 setup)

### 1. Apply Database Migrations (if not done in Phase 2)

In the Supabase SQL Editor:
```
supabase/migrations/001_extensions.sql
supabase/migrations/002_schema.sql
supabase/seed/seed_departments.sql
```

### 2. Configure Environment Variables

```bash
# Backend
cd backend && cp ../.env.example .env
# Fill in: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
#           SUPABASE_ANON_KEY, SUPABASE_STORAGE_BUCKET

# Frontend
cd frontend && cp ../.env.example .env.local
# Fill in: NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_SUPABASE_URL,
#           NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### 3. Create Supabase Storage Bucket

In the Supabase dashboard → Storage → Create bucket:
- Name: `report-images`
- Public: ✓ (so uploaded photos are accessible via public URL)

### 4. Start the Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: **http://localhost:8000** | Swagger: **http://localhost:8000/docs**

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: **http://localhost:3000**

### 6. Test Report Submission

1. Open **http://localhost:3000/report/new**
2. Fill in description (min 10 chars), add a photo, enter lat/lng
3. Click Submit — you'll be redirected to `/track/[token]`
4. The tracking page shows report status, category, and updates

### 7. Run Tests

```bash
cd backend
pytest                     # 9 pass (validation), 25 skip (DB)
pytest tests/test_reports.py -v   # report + upload tests
```

## Project Structure

```
frontend/          Next.js resident portal and admin dashboard
  app/report/new/  Report submission form
  app/track/[token]/ Public status tracking page
backend/           FastAPI API
  app/api/         Route handlers (reports, tracking, upload, departments)
  app/services/    Business logic
  app/db/          SQLAlchemy + Supabase client + image upload helper
  scripts/         DB check and seed scripts
mcp-server/        city-ops-mcp MCP server (Phase 7)
supabase/
  migrations/      001_extensions.sql, 002_schema.sql
  seed/            seed_departments.sql
docs/              Supporting documentation
.claude/           Claude agents, skills, commands, hooks
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check |
| POST | `/api/reports` | None | Submit a report |
| GET | `/api/reports` | None | List reports |
| GET | `/api/tracking/{token}` | None | Resident tracking |
| POST | `/api/upload/image` | None | Upload report photo |
| GET | `/api/departments` | None | List departments |

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
