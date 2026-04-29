# CivicFix

CivicFix is an AI-powered civic issue reporting and routing platform. Residents can submit local infrastructure issues with photos, descriptions, voice, and map locations. AI classifies the issue, estimates urgency, detects duplicates, routes the report to the right department, and generates summaries for city staff.

## Core Features

- Resident report submission
- Image, text, and optional voice input
- Map pin location capture
- AI issue classification
- Severity scoring
- Department routing
- Duplicate detection using embeddings
- Admin dashboard with map and filters
- Status workflow
- Resident tracking page
- Realtime dashboard updates
- Email/SMS notifications
- Custom MCP server for city operations tools

## Tech Stack

- Frontend: Next.js, React, TypeScript, Tailwind
- Backend: FastAPI, Python, Pydantic
- Database: Supabase Postgres, PostGIS, pgvector
- Maps: Mapbox or OpenStreetMap
- AI: Vision model, LLM, embeddings
- Notifications: Twilio/email
- Realtime: Supabase Realtime
- MCP: custom `city-ops-mcp` server

## Project Structure

See `CLAUDE.md` and the `docs/` directory for architecture, API contracts, AI pipeline details, and implementation plans.

## MVP Demo Flow

1. Resident submits a flooded sidewalk, pothole, broken light, trash overflow, or unsafe sidewalk report.
2. AI classifies the report and assigns severity.
3. AI routes it to a department.
4. Admin sees the report on a map.
5. Admin reviews AI summary and duplicate suggestions.
6. Admin updates status.
7. Resident sees status update.
