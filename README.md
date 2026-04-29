# CivicFix

AI-powered civic issue reporting and routing platform. Residents submit local infrastructure issues with photos, descriptions, and map locations. AI classifies the issue, estimates severity, detects duplicates, and routes the report to the correct city department.

## Current Phase: Phase 1 — Foundation

The backend and frontend are initialized with placeholder routes and pages. Supabase schema migrations are ready to apply. Full functionality is built in Phases 3–6.

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Supabase project (free tier works for development)

### Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env — fill in DATABASE_URL and SUPABASE_* values

# Start dev server
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**
Swagger docs at **http://localhost:8000/docs**
Health check: **GET http://localhost:8000/health**

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp ../.env.example .env.local
# Edit .env.local — fill in NEXT_PUBLIC_* values

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:3000**

### Database (Supabase)

1. Create a project at [supabase.com](https://supabase.com)
2. In the SQL editor, run migrations in order:
   ```
   supabase/migrations/001_extensions.sql
   supabase/migrations/002_schema.sql
   supabase/seed/seed_departments.sql
   ```
3. Copy the project URL and keys into your `.env` / `.env.local` files

### Running Tests

```bash
cd backend
pytest
```

## Project Structure

```
frontend/          Next.js resident and admin UI
backend/           FastAPI backend API
mcp-server/        city-ops-mcp MCP server (Phase 7)
supabase/          Database migrations and seed data
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
