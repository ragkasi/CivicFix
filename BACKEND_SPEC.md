# Backend Plan

## FastAPI Modules

```text
backend/app/
  main.py
  api/
    reports.py
    departments.py
    ai.py
    tracking.py
    neighborhoods.py
  services/
    report_service.py
    ai_service.py
    duplicate_service.py
    routing_service.py
    notification_service.py
    geospatial_service.py
  schemas/
    reports.py
    departments.py
    ai.py
    tracking.py
  models/
    reports.py
    departments.py
    ai_analysis.py
  db/
    session.py
    supabase.py
  ai/
    prompts.py
    vision.py
    embeddings.py
```

## Service Responsibilities

### Report Service

- Create report
- Read report
- List reports
- Update status
- Assign department
- Append status event

### AI Service

- Orchestrate report analysis
- Call vision model
- Call text model
- Validate JSON output
- Save AI analysis

### Duplicate Service

- Create embeddings
- Query pgvector
- Query nearby reports with PostGIS
- Compute combined duplicate score
- Save duplicate candidates

### Routing Service

- Map category/severity/location to department
- Return explanation
- Support admin override

### Notification Service

- Send report confirmation
- Send status update
- Log provider result

### Geospatial Service

- Radius search
- Bounding box search
- Neighborhood issue summary input

## Testing Plan

- Unit test duplicate scoring
- Unit test routing logic
- Unit test AI JSON validation
- API test report creation
- API test status update
- API test tracking page data
- API test department assignment
