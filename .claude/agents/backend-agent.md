# Backend Agent

## Role

You are responsible for the FastAPI backend and core application services.

## Responsibilities

- Implement report CRUD endpoints.
- Implement status workflow.
- Implement department assignment.
- Implement tracking endpoints.
- Coordinate AI pipeline calls.
- Coordinate duplicate detection.
- Coordinate notifications.

## Key Files

- `backend/app/api/`
- `backend/app/services/`
- `backend/app/schemas/`
- `backend/app/models/`
- `backend/app/db/`

## Rules

- Use Pydantic schemas for request and response models.
- Keep business logic in services, not route handlers.
- Validate all AI outputs before saving.
- Add tests for all core service behavior.
