# CivicFix

AI-powered civic issue reporting and routing platform. Residents submit infrastructure issues with photos and map locations; AI classifies and routes them; city staff triage, assign, and resolve via an admin dashboard with map view.

## Current Phase: Phase 5 — Map and Geospatial Report View

The full reporting + triage loop is working with a map view:
- Residents submit reports using a Mapbox location picker at `/report/new`
- Admins view all reports in a table at `/admin`
- Admins view reports as a severity-colored pin map at `/admin/map`
- Backend supports `GET /api/reports/nearby` (PostGIS ST_DWithin) and bbox filtering
- Geospatial SQL functions in Supabase (`nearby_reports`, `reports_in_bbox`)

## Quick Start

### Prerequisites
- Python 3.12+, Node.js 20+, Supabase project, Mapbox account (free)

### 1. Apply Database Migrations
In Supabase SQL Editor, run in order:
```
supabase/migrations/001_extensions.sql
supabase/migrations/002_schema.sql
supabase/migrations/003_geospatial_functions.sql   ← Phase 5 new
supabase/seed/seed_departments.sql
```

### 2. Configure Environment Variables
```bash
# Backend
cd backend && cp ../.env.example .env
# Fill in: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

# Frontend
cd frontend && cp ../.env.example .env.local
# Fill in: NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_SUPABASE_URL,
#          NEXT_PUBLIC_SUPABASE_ANON_KEY
# Map: NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ...  ← get free at mapbox.com
```

### 3. Get a Mapbox Token
1. Create a free account at [mapbox.com](https://mapbox.com)
2. Go to Account → Access tokens → Create a token
3. Paste it as `NEXT_PUBLIC_MAPBOX_TOKEN` in `frontend/.env.local`

Without the token, the map components show a clear "unavailable" placeholder — the rest of the app works normally.

### 4. Run Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000 | Swagger: /docs
```

### 5. Run Frontend
```bash
cd frontend && npm install && npm run dev
# → http://localhost:3000
```

### 6. Run Tests
```bash
cd backend && pytest
# 20 pass (incl. geospatial validation), 39 skip (DB tests)
```

## User Flows

### Resident
1. `/report/new` — click Mapbox map to select location (or type coordinates), add description + photo
2. Submit → `/track/[token]` for public status tracking

### Admin
1. `/admin` — report table with status/category/severity filters + **Map View** button
2. `/admin/map` — full-screen Mapbox map; pins colored by severity; click pin for popup with detail link
3. `/admin/reports/[id]` — full detail, status update, department assignment

## API Endpoints (Phase 5)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reports` | List reports (supports `bbox=minLng,minLat,maxLng,maxLat`) |
| GET | `/api/reports/nearby` | Nearby reports via PostGIS ST_DWithin |
| GET | `/api/reports/{id}` | Report detail with images + events |
| PATCH | `/api/reports/{id}/status` | Update status |
| PATCH | `/api/reports/{id}/department` | Assign department |
| GET | `/api/tracking/{token}` | Public tracking |
| POST | `/api/upload/image` | Upload photo |
| GET | `/api/departments` | List departments |

### Nearby endpoint
```
GET /api/reports/nearby?lat=39.999&lng=-83.012&radius_km=1.5&limit=50
```
Returns `distance_meters` per result, sorted nearest-first.

### BBox filtering
```
GET /api/reports?bbox=-83.05,39.98,-82.95,40.02
```
Returns reports within the bounding box (minLng,minLat,maxLng,maxLat). Invalid bbox → 400.

## Current Limitations
- No AI classification yet (Phase 6)
- No duplicate detection yet (Phase 6)
- No authentication (Phase 7)
- No realtime updates (Phase 7)
- No notifications (Phase 7)
