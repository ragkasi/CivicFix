# Skill: Geospatial Analysis

## Purpose

Use PostGIS to support map views, nearby report search, and neighborhood summaries.

## Use Cases

- Find reports inside map bounds.
- Find reports within radius of a submitted report.
- Cluster reports by area.
- Summarize recurring issues in a neighborhood.

## Query Patterns

- Radius search with `ST_DWithin`
- Distance sorting with `ST_Distance`
- Bounding box filtering with `ST_MakeEnvelope`
- Map clustering at frontend or database layer

## Guardrails

- Store coordinates using SRID 4326.
- Validate latitude and longitude.
- Do not infer exact location from vague text without user confirmation.
