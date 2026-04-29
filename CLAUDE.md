# CivicFix Claude Project Guide

## Project Overview

CivicFix is an AI-powered local issue reporting and routing platform. Residents submit infrastructure issues using photos, text, voice, and map pins. The system uses AI to classify the issue, estimate severity, detect duplicates, extract location context, route the report to the correct department, and generate summaries for city staff.

The product has two main surfaces:

1. Resident portal for submitting and tracking reports.
2. Admin dashboard for triage, map-based monitoring, duplicate review, department routing, and status workflows.

The project should be built as a practical, deployable civic-tech platform, not just a chatbot demo.

## Primary Goals

- Build a working resident report flow.
- Build a real admin operations dashboard.
- Use AI meaningfully inside the workflow.
- Support geospatial report discovery with PostGIS.
- Support duplicate detection with embeddings and pgvector.
- Support realtime status updates with Supabase Realtime.
- Support notifications with email/Twilio.
- Include a custom MCP server called `city-ops-mcp`.

## Tech Stack

### Frontend

- Next.js or React
- TypeScript
- Tailwind CSS
- Mapbox GL JS or OpenStreetMap/Leaflet
- Supabase client

### Backend

- FastAPI
- Python
- Pydantic
- SQLAlchemy or Supabase client
- OpenAI-compatible LLM/Vision APIs

### Database

- Supabase Postgres
- PostGIS for geospatial queries
- pgvector for duplicate detection embeddings
- Supabase Storage for uploaded images
- Supabase Realtime for live dashboard updates

### AI

- Vision model for image classification
- LLM for report extraction, summarization, severity scoring, and routing
- Embeddings for semantic duplicate detection

### Notifications

- Twilio SMS
- Email provider such as Resend, SendGrid, or Supabase email flows

### MCP

- Custom MCP server: `city-ops-mcp`
- Tools:
  - `classify_report`
  - `detect_duplicate_reports`
  - `route_to_department`
  - `summarize_neighborhood_issues`
  - `generate_resolution_update`
  - `get_report_context`

## Repository Structure

```text
civicfix/
  CLAUDE.md
  README.md
  .env.example
  frontend/
    app/
    components/
    lib/
    hooks/
    types/
  backend/
    app/
      api/
      services/
      models/
      schemas/
      ai/
      db/
  mcp-server/
    tools/
  supabase/
    migrations/
    seed.sql
  docs/
    product-requirements.md
    architecture.md
    database-schema.md
    api-contract.md
    ai-pipeline.md
    mcp-design.md
    frontend-plan.md
    backend-plan.md
    deployment-plan.md
    demo-script.md
  .claude/
    agents/
    commands/
    skills/
    hooks/
```

## Core User Flows

### Resident Report Submission

1. Resident opens submission page.
2. Resident uploads photo.
3. Resident enters description or records voice.
4. Resident selects location using map pin or browser geolocation.
5. Backend stores raw report.
6. AI pipeline classifies and enriches report.
7. Duplicate detection checks nearby similar reports.
8. Report appears in admin dashboard.
9. Resident receives tracking link.

### Admin Triage Flow

1. Admin opens dashboard.
2. Admin sees report map and table.
3. Admin filters by status, severity, category, department, or date.
4. Admin opens report detail view.
5. Admin reviews AI summary, category, severity, duplicate suggestions, and recommended department.
6. Admin assigns report to a department.
7. Admin updates status.
8. Resident receives update.

### Resident Tracking Flow

1. Resident opens tracking page.
2. Resident sees current status.
3. Resident sees public-facing summary.
4. Resident receives updates when status changes.

## AI Pipeline Contract

Whenever a report is submitted, create a structured AI analysis object:

```json
{
  "category": "Drainage/Flooding",
  "severity": "High",
  "department": "Public Works",
  "summary": "Resident reports recurring sidewalk flooding near a bus stop after rain.",
  "recommended_action": "Schedule inspection for drainage blockage or grading issue.",
  "confidence": 0.91,
  "location_notes": "Near bus stop mentioned by user",
  "duplicate_candidates": []
}
```

## Development Principles

- Build vertical slices before broad feature expansion.
- Keep all AI outputs structured as JSON.
- Save both raw user input and AI-enriched output.
- Never overwrite user-submitted data with AI-inferred data.
- Every AI inference should include confidence and reasoning fields where useful.
- Admins must be able to override AI category, severity, department, and duplicate grouping.
- Separate resident-facing language from internal admin notes.
- Do not expose private admin notes to residents.

## MVP Definition

The MVP is complete when:

1. A resident can submit a report with image, description, and location.
2. The backend stores the report.
3. AI generates category, severity, department, summary, and recommended action.
4. The admin dashboard displays reports on a map and table.
5. Admins can update status.
6. Residents can view a tracking page.
7. Status updates are reflected in realtime or near-realtime.

## Claude Working Instructions

When generating code:

- Prefer complete files over fragments.
- Use TypeScript on the frontend.
- Use Pydantic schemas on the backend.
- Keep API contracts documented.
- Add comments for non-obvious logic.
- Avoid mock data unless explicitly marked as mock/demo.
- When using placeholder AI calls, isolate them behind service interfaces.
- Make all environment variables explicit in `.env.example`.
- Prioritize testable service functions.
- Keep folder structure aligned with this file.

When planning features:

- Start with data model changes.
- Then define API endpoints.
- Then define frontend states.
- Then define AI service behavior.
- Then define tests.

