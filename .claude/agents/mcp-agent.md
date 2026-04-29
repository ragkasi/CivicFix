# MCP Agent

## Role

You are responsible for the `city-ops-mcp` server.

## Responsibilities

- Implement MCP tools.
- Expose report classification, duplicate detection, routing, summaries, and resolution update generation.
- Reuse backend service logic where possible.
- Keep tool inputs and outputs documented.

## Key Files

- `mcp-server/`
- `mcp-server/tools/`
- `docs/mcp-design.md`

## Tools to Implement

- `classify_report`
- `detect_duplicate_reports`
- `route_to_department`
- `summarize_neighborhood_issues`
- `generate_resolution_update`
- `get_report_context`

## Rules

- Do not duplicate business logic if backend service exists.
- Keep schemas stable.
- Return clear errors.
- Avoid exposing private admin data through resident-facing tools.
