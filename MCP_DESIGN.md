# city-ops-mcp Design

## Purpose

`city-ops-mcp` exposes city operations tools that allow an MCP-capable assistant to classify reports, detect duplicates, route reports, summarize neighborhoods, and draft resident updates.

## Tools

### classify_report

Input:

```json
{
  "description": "string",
  "image_url": "string|null",
  "latitude": "number|null",
  "longitude": "number|null"
}
```

Output:

```json
{
  "category": "string",
  "severity": "string",
  "summary": "string",
  "confidence": "number"
}
```

### detect_duplicate_reports

Input:

```json
{
  "report_id": "uuid",
  "radius_meters": 500,
  "min_similarity": 0.78
}
```

Output:

```json
{
  "duplicates": [
    {
      "report_id": "uuid",
      "combined_score": 0.88,
      "distance_meters": 42,
      "reason": "Similar flooding report near same bus stop."
    }
  ]
}
```

### route_to_department

Input:

```json
{
  "category": "Drainage/Flooding",
  "severity": "High",
  "location": "Summit Street near bus stop"
}
```

Output:

```json
{
  "department": "Public Works",
  "reason": "Drainage and flooding issues are handled by Public Works.",
  "priority": "High"
}
```

### summarize_neighborhood_issues

Input:

```json
{
  "latitude": 39.999,
  "longitude": -83.012,
  "radius_meters": 1000,
  "days": 30
}
```

Output:

```json
{
  "summary": "The area has recurring drainage and sidewalk reports, mostly after rainfall.",
  "top_categories": ["Drainage/Flooding", "Sidewalk Damage"],
  "recommended_focus": "Inspect drainage infrastructure near transit stops."
}
```

### generate_resolution_update

Input:

```json
{
  "report_id": "uuid",
  "new_status": "resolved",
  "internal_note": "Crew cleared blocked drain."
}
```

Output:

```json
{
  "public_update": "A city crew reviewed the issue and cleared the blocked drain. The report has been marked resolved."
}
```

### get_report_context

Input:

```json
{
  "report_id": "uuid"
}
```

Output:

```json
{
  "report": {},
  "ai_analysis": {},
  "status_history": [],
  "duplicate_candidates": []
}
```

## Implementation Rule

The MCP tools should call shared backend services when possible. Do not duplicate classification, routing, or duplicate detection logic in two places.
