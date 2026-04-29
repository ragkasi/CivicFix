# API Contract

Base URL: `/api`

## Reports

### Create Report

`POST /reports`

Request:

```json
{
  "description": "This keeps happening near the bus stop after rain.",
  "latitude": 39.999,
  "longitude": -83.012,
  "address": "1986 Summit St",
  "image_paths": ["report-images/example.jpg"],
  "contact_email": "resident@example.com",
  "contact_phone": "+15555555555"
}
```

Response:

```json
{
  "id": "uuid",
  "status": "submitted",
  "tracking_token": "token"
}
```

### Get Report

`GET /reports/{report_id}`

Returns report, images, AI analysis, duplicate candidates, and status history.

### List Reports

`GET /reports?status=&category=&severity=&department_id=&bbox=&limit=&offset=`

Supports dashboard filtering and map bounds.

### Update Report Status

`PATCH /reports/{report_id}/status`

Request:

```json
{
  "status": "assigned",
  "note": "Assigned to Public Works for inspection.",
  "public_note": "This report has been assigned for review."
}
```

### Assign Department

`PATCH /reports/{report_id}/department`

Request:

```json
{
  "department_id": "uuid"
}
```

## AI

### Analyze Report

`POST /ai/reports/{report_id}/analyze`

Runs classification, severity scoring, routing, summary generation, embedding creation, and duplicate detection.

### Detect Duplicates

`POST /ai/reports/{report_id}/duplicates`

Returns likely duplicate candidates.

## Departments

### List Departments

`GET /departments`

### Create Department

`POST /departments`

Admin only.

## Tracking

### Public Tracking Page Data

`GET /tracking/{tracking_token}`

Returns resident-safe report status and public notes.

## Neighborhood Summary

`GET /neighborhoods/summary?lat=&lng=&radius_m=&category=&days=`

Returns AI-generated summary of local issue trends in a radius.
