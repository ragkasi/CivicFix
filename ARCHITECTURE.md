# CivicFix Architecture

## System Overview


Resident Web App
    |
    v
FastAPI Backend ---- AI Services
    |                 |
    v                 v
Supabase Postgres + PostGIS + pgvector
    |
    v
Admin Dashboard via Supabase Realtime
    |
    v
Notifications via Twilio/Email

MCP Server: city-ops-mcp
    |
    v
City operations tools wrapping classification, routing, duplicate detection, summaries, and updates


## Main Components

### Frontend

The frontend contains both resident and admin experiences. It should use shared components for maps, report cards, status badges, image previews, and filters.

### Backend

The backend owns report creation, AI orchestration, department routing, duplicate detection, notification triggering, and secure admin operations.

### Database

Supabase Postgres stores report data, status history, departments, AI analysis, duplicate groups, user profiles, and notification logs.

### Geospatial Layer

PostGIS supports radius queries, nearby report lookup, map bounds filtering, and neighborhood issue summaries.

### Embeddings Layer

pgvector supports semantic duplicate detection. The duplicate score should combine embedding similarity, geospatial proximity, category similarity, and recency.

### Realtime Layer

Supabase Realtime publishes changes to reports and status events so the admin dashboard can update without refresh.

### MCP Layer

The MCP server exposes city operations tools that can be called by Claude or another MCP-capable agent. These tools should use the backend service layer, not duplicate business logic.

## Data Flow: Report Submission

1. Frontend uploads image to Supabase Storage or backend upload endpoint.
2. Frontend submits report metadata to FastAPI.
3. FastAPI saves raw report.
4. AI service classifies and summarizes report.
5. Embedding service creates report embedding.
6. Duplicate service queries pgvector and PostGIS.
7. Routing service recommends department.
8. Backend saves AI analysis.
9. Supabase Realtime notifies admin dashboard.
10. Notification service sends confirmation to resident.

## Design Rules

- Store raw report separately from AI-enriched output.
- AI recommendations must be editable by admins.
- All status changes should be appended to status history.
- Never delete reports permanently in MVP; soft delete instead.
- Geospatial fields should use PostGIS geometry/geography types.
