# Database Schema Plan

## Extensions

```sql
create extension if not exists postgis;
create extension if not exists vector;
create extension if not exists pgcrypto;
```

## Tables

### profiles

Stores resident and admin user metadata.

```sql
create table profiles (
  id uuid primary key,
  email text unique,
  full_name text,
  role text not null default 'resident',
  created_at timestamptz default now()
);
```

### departments

```sql
create table departments (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  category_coverage text[] default '{}',
  contact_email text,
  created_at timestamptz default now()
);
```

### reports

```sql
create table reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  title text,
  description text not null,
  category text,
  severity text,
  status text not null default 'submitted',
  department_id uuid references departments(id),
  latitude double precision not null,
  longitude double precision not null,
  address text,
  geom geography(Point, 4326),
  is_duplicate boolean default false,
  duplicate_group_id uuid,
  public_tracking_token text unique default encode(gen_random_bytes(16), 'hex'),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

### report_images

```sql
create table report_images (
  id uuid primary key default gen_random_uuid(),
  report_id uuid references reports(id) on delete cascade,
  storage_path text not null,
  public_url text,
  created_at timestamptz default now()
);
```

### ai_analysis

```sql
create table ai_analysis (
  id uuid primary key default gen_random_uuid(),
  report_id uuid references reports(id) on delete cascade,
  ai_category text,
  ai_severity text,
  ai_department text,
  ai_summary text,
  recommended_action text,
  resident_friendly_summary text,
  confidence_score numeric,
  reasoning jsonb,
  embedding vector(1536),
  created_at timestamptz default now()
);
```

### duplicate_groups

```sql
create table duplicate_groups (
  id uuid primary key default gen_random_uuid(),
  canonical_report_id uuid references reports(id),
  summary text,
  created_at timestamptz default now()
);
```

### report_duplicate_candidates

```sql
create table report_duplicate_candidates (
  id uuid primary key default gen_random_uuid(),
  report_id uuid references reports(id) on delete cascade,
  candidate_report_id uuid references reports(id) on delete cascade,
  semantic_score numeric,
  distance_meters numeric,
  combined_score numeric,
  created_at timestamptz default now()
);
```

### report_status_events

```sql
create table report_status_events (
  id uuid primary key default gen_random_uuid(),
  report_id uuid references reports(id) on delete cascade,
  old_status text,
  new_status text not null,
  note text,
  public_note text,
  changed_by uuid references profiles(id),
  created_at timestamptz default now()
);
```

### notifications

```sql
create table notifications (
  id uuid primary key default gen_random_uuid(),
  report_id uuid references reports(id) on delete cascade,
  channel text not null,
  recipient text not null,
  subject text,
  body text,
  status text default 'pending',
  provider_response jsonb,
  created_at timestamptz default now(),
  sent_at timestamptz
);
```

## Indexes

```sql
create index reports_geom_idx on reports using gist (geom);
create index reports_status_idx on reports(status);
create index reports_category_idx on reports(category);
create index reports_severity_idx on reports(severity);
create index ai_analysis_embedding_idx on ai_analysis using ivfflat (embedding vector_cosine_ops);
```
