# CivicFix — Frontend

Next.js 15 application for the CivicFix civic issue reporting platform.

## Stack

- Next.js 15 (App Router, TypeScript)
- Tailwind CSS
- shadcn/ui components
- Supabase JS client (Phase 4+)
- Mapbox GL JS (Phase 3b+)

## Getting Started

```bash
cd frontend

npm install

cp ../.env.example .env.local
# Fill in:
#   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
#   NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
#   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
#   NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ...  (Phase 3b)

npm run dev
```

Frontend: **http://localhost:3000**

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI backend URL (default: `http://localhost:8000`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox token for map UI (Phase 3b+) |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run type-check` | TypeScript check (no emit) |
| `npm run lint` | ESLint |

## Pages (Phase 3)

| Route | Description |
|-------|-------------|
| `/` | Landing page — links to report form and admin dashboard |
| `/report/new` | Resident report submission form |
| `/track/[token]` | Public report status tracking page |
| `/admin` | Admin dashboard placeholder (Phase 4) |

## Report Submission Flow

1. Resident fills in description, optional photo, coordinates, optional address
2. If a photo is selected: `POST /api/upload/image` → receives `storage_path`
3. `POST /api/reports` with `image_path: storage_path`
4. On success → redirect to `/track/[tracking_token]`

## Key Files

```
app/
  page.tsx              Landing page
  report/new/page.tsx   Resident report form (client component)
  track/[token]/page.tsx Report tracking page (client component)
  admin/page.tsx        Admin placeholder
components/ui/
  button.tsx            shadcn-style Button
  badge.tsx             StatusBadge and SeverityBadge
lib/
  api.ts                Typed API client + all TypeScript types
  utils.ts              cn() utility
types/
  index.ts              Re-exports from lib/api.ts
```
