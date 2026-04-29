# Frontend Plan

## Pages

### `/`

Landing page explaining CivicFix and linking to report submission.

### `/report/new`

Resident report submission form.

Fields:

- Image upload
- Description
- Optional voice transcription
- Map pin
- Contact email/phone

### `/track/[token]`

Resident tracking page.

Shows:

- Report status
- Public notes
- Timeline
- Resident-friendly summary

### `/admin`

Admin dashboard.

Shows:

- Report map
- Report table
- Filters
- Severity/category/status counts

### `/admin/reports/[id]`

Report detail view.

Shows:

- Image
- Description
- Location
- AI summary
- Category/severity/department
- Duplicate candidates
- Status history
- Status update form

## Components

- `ReportForm`
- `ImageUploader`
- `LocationPickerMap`
- `ReportMap`
- `ReportTable`
- `ReportCard`
- `StatusBadge`
- `SeverityBadge`
- `CategoryFilter`
- `DuplicateCandidateList`
- `StatusTimeline`
- `DepartmentSelect`

## State Management

Use server actions or API client wrappers for backend calls. Use Supabase Realtime subscriptions for admin report updates.

## Design Style

- Clean civic dashboard aesthetic
- Map-first admin experience
- Strong status visibility
- Use color carefully for severity and status
- Keep resident flow simple and mobile-friendly
