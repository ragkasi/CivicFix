# Command: Generate API

Use this command when generating or modifying FastAPI endpoints.

## Required Output

For each endpoint, include:

Method:
Path:
Purpose:
Request body:
Response body:
Validation:
Service method:
Database tables touched:
Errors:
Tests:

## Rules

- Keep route handlers thin.
- Use Pydantic schemas.
- Put business logic in services.
- Return consistent errors.
- Do not expose internal implementation details to frontend.
