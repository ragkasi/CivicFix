
# AI Pipeline

## Overview

The AI pipeline enriches resident reports with structured information that helps city staff triage and route issues.

AI should be treated as a recommendation layer, not the final authority.

## Inputs

A report may include:

- Text description.
- Uploaded image.
- Location coordinates.
- Address.
- Optional voice transcript.
- Nearby historical reports.

## Outputs

The AI pipeline should return:

{
  "category": "flooding",
  "severity": "high",
  "department_slug": "public_works",
  "summary": "Resident reports recurring sidewalk flooding near a bus stop after rain.",
  "recommended_action": "Schedule a drainage inspection.",
  "confidence": 0.91,
  "reasoning_summary": "The description mentions flooding after rain near a pedestrian area."
}

