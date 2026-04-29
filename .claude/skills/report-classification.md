# Skill: Report Classification

## Purpose

Classify a resident report into a civic issue category and severity level.

## Inputs

- Description
- Optional image URL or image analysis
- Location metadata

## Outputs

- Category
- Severity
- Confidence
- Reasoning
- Recommended action

## Categories

- Pothole/Road Damage
- Drainage/Flooding
- Broken Streetlight
- Sidewalk Damage
- Trash Overflow
- Damaged Sign
- Graffiti
- Fallen Tree/Obstruction
- Snow/Ice Hazard
- Other

## Severity Rules

- Critical: immediate danger, major flooding, blocked emergency access, exposed utilities
- High: safety risk, recurring flooding, blocked sidewalk, hazardous road damage
- Medium: moderate inconvenience or worsening issue
- Low: cosmetic issue or non-urgent maintenance

## Guardrails

- Return JSON only.
- Do not invent exact location details.
- Include confidence.
- Use `Other` when uncertain.
