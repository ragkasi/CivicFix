# Skill: Department Routing

## Purpose

Recommend the correct city department for a report.

## Initial Routing Rules

- Pothole/Road Damage -> Public Works or Streets Department
- Drainage/Flooding -> Public Works
- Broken Streetlight -> Utilities or Public Works
- Sidewalk Damage -> Public Works
- Trash Overflow -> Sanitation
- Damaged Sign -> Transportation
- Graffiti -> Code Enforcement or Sanitation
- Fallen Tree/Obstruction -> Parks or Public Works
- Snow/Ice Hazard -> Public Works
- Other -> 311/General Services

## Output

```json
{
  "department": "Public Works",
  "priority": "High",
  "reason": "Drainage and sidewalk flooding are handled by Public Works."
}
```

## Guardrails

- Return recommendation, not final assignment.
- Admin must be able to override.
- Include reason for routing.
