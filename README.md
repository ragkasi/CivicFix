# CivicFix

AI-powered civic issue reporting and routing platform. Residents submit local infrastructure issues; AI classifies, routes, and deduplicates. City staff triage, assign, and resolve reports through an admin dashboard.

## Current Phase: Phase 4 — Admin Report Dashboard

The full resident submission + admin triage loop is working:
- Residents submit reports at `/report/new`
- Reports are stored in Supabase with a tracking token
- Admins view all reports at `/admin`, filter by status/category/severity
- Admins open report detail at `/admin/reports/[id]`
- Admins update report status and assign departments
- Every status change is logged to `status_events`
- Residents track their report at `/track/[token]`

AI classification, map view, duplicate detection, and realtime updates come in later phases.

## Local Development

### Prerequisites
- Python 3.12+, Node.js 20+
- Supabase project with migrations applied

### Apply Database Migrations (once)
In Supabase SQL Editor, run in order:
```
supabase/migrations/001_extensions.sql
supabase/migrations/002_schema.sql
supabase/seed/seed_departments.sql
```

### Configure Environment Variables
```bash
# Backend
cd backend && cp ../.env.example .env
# Fill in: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

# Frontend
cd frontend && cp ../.env.example .env.local
# Fill in: NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### Run Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000 | Swagger: /docs
```

### Run Frontend
```bash
cd frontend
npm install && npm run dev
# → http://localhost:3000
```

### Run Tests
```bash
cd backend
pytest           # 9 pass, 36 skip (DB tests need credentials)
pytest -v        # verbose
```

## User Flows

### Resident
1. `/report/new` — fill description, optional photo, lat/lng, optional contact
2. Submit → redirect to `/track/[token]`
3. `/track/[token]` — see status, category, public notes

### Admin
1. `/admin` — table of all reports with filters and pagination
2. Click **View →** to open `/admin/reports/[id]`
3. Update status + optional public note → resident's tracking page reflects change
4. Assign department → department shown in table and detail
5. Status history timeline shows all changes

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/reports` | Submit a report |
| GET | `/api/reports` | List reports (filters: status, category, severity, dept) |
| GET | `/api/reports/{id}` | Report detail with images + status events |
| PATCH | `/api/reports/{id}/status` | Update status + log event |
| PATCH | `/api/reports/{id}/department` | Assign department |
| GET | `/api/tracking/{token}` | Public resident tracking |
| POST | `/api/upload/image` | Upload report photo |
| GET | `/api/departments` | List departments |

## Current Limitations
- No AI classification yet (Phase 5)
- No map view yet (Phase 5)
- No duplicate detection yet (Phase 5)
- No authentication/login (Phase 6)
- No realtime dashboard updates (Phase 6)
- No notifications (Phase 6)

## Documentation

| Doc | Description |
|-----|-------------|
| [CLAUDE.md](CLAUDE.md) | Project guide for Claude |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture |
| [API_CONTRACT.md](API_CONTRACT.md) | API endpoint contracts |
| [DATA_MODEL.md](DATA_MODEL.md) | Database schema |
| [AI_PIPELINE.md](AI_PIPELINE.md) | AI classification pipeline |
| [FRONTEND_SPEC.md](FRONTEND_SPEC.md) | Frontend pages and components |
| [BACKEND_SPEC.md](BACKEND_SPEC.md) | Backend structure |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Phase-by-phase plan |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Demo walkthrough |
