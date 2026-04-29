# CivicFix Product Requirements

## Problem

Cities receive vague, incomplete, or misrouted resident complaints about infrastructure issues such as potholes, flooding, broken streetlights, unsafe sidewalks, overflowing trash, damaged signs, and blocked drains. CivicFix helps residents submit better reports and helps city staff triage them faster.

## Target Users

### Residents

Residents need a simple way to report local issues and track what happens afterward.

### City Staff/Admins

City staff need a dashboard to view, filter, triage, route, and resolve reports.

### Department Operators

Departments need clear summaries, recommended actions, location context, and priority information.

## Core Features

### Resident Portal

- Create report
- Upload image
- Add text description
- Optional voice transcription
- Select location with map pin
- Submit contact info optionally
- View tracking page
- Receive status notifications

### Admin Dashboard

- Report list
- Map view
- Severity/category/status filters
- Department assignment
- AI-generated summary
- Duplicate suggestions
- Status workflow
- Resolution notes
- Public-facing update generation

### AI Features

- Image classification
- Text extraction and normalization
- Severity scoring
- Department routing
- Duplicate detection
- Neighborhood issue summarization
- Resolution update drafting

## Report Categories

Initial categories:

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

## Severity Levels

- Low: cosmetic or non-urgent issue
- Medium: inconvenience or moderate safety concern
- High: safety risk, access blockage, flooding, or urgent public issue
- Critical: immediate danger or major infrastructure failure

## Status Workflow

- Submitted
- Reviewed
- Assigned
- In Progress
- Resolved
- Closed
- Duplicate
- Rejected

## MVP Acceptance Criteria

- Resident can submit report with photo, text, and location.
- Report is persisted in database.
- AI returns structured classification and summary.
- Admin can view report on map and table.
- Admin can update status.
- Resident tracking page reflects status.
