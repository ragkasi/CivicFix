# Skill: Duplicate Detection

## Purpose

Find reports that likely describe the same real-world issue.

## Inputs

- Report ID
- Report embedding
- Category
- Latitude/longitude
- Created date

## Method

1. Query nearby reports using PostGIS radius search.
2. Query semantically similar reports using pgvector.
3. Combine candidates.
4. Score using semantic similarity, distance, category match, and recency.
5. Return candidates for admin review.

## Combined Score

```text
combined_score =
  0.50 * semantic_similarity +
  0.25 * location_score +
  0.15 * category_score +
  0.10 * recency_score
```

## Guardrails

- Do not automatically merge reports.
- Do not mark reports duplicate without admin confirmation.
- Always show explanation for why a report is a possible duplicate.
