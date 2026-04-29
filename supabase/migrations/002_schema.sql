-- CivicFix core schema.
-- Run after 001_extensions.sql.
-- Requires: postgis, vector, pgcrypto.

-- ─── Profiles ────────────────────────────────────────────────────────────────
-- Extends Supabase auth.users. Populated via auth trigger in a later migration.

create table if not exists profiles (
  id          uuid primary key,
  email       text unique,
  full_name   text,
  role        text not null default 'resident' check (role in ('resident', 'admin', 'staff')),
  created_at  timestamptz not null default now()
);

-- ─── Departments ─────────────────────────────────────────────────────────────

create table if not exists departments (
  id                uuid primary key default gen_random_uuid(),
  name              text not null,
  description       text,
  category_coverage text[] not null default '{}',
  contact_email     text,
  created_at        timestamptz not null default now()
);

-- ─── Reports ─────────────────────────────────────────────────────────────────

create table if not exists reports (
  id                    uuid primary key default gen_random_uuid(),
  user_id               uuid references profiles(id) on delete set null,
  department_id         uuid references departments(id) on delete set null,
  description           text not null,
  category              text check (category in (
                          'pothole','streetlight','flooding','sidewalk_damage',
                          'trash_overflow','damaged_sign','road_hazard',
                          'graffiti','snow_or_ice','other'
                        )),
  severity              text check (severity in ('low','medium','high','critical')),
  status                text not null default 'submitted' check (status in (
                          'submitted','reviewed','assigned','in_progress',
                          'resolved','duplicate','rejected'
                        )),
  -- Coordinates stored as plain floats for easy filtering
  latitude              double precision not null,
  longitude             double precision not null,
  address               text,
  -- PostGIS geography column for radius queries and map display
  geom                  geography(Point, 4326),
  -- Public token for resident tracking page (no auth required)
  public_tracking_token text unique not null default encode(gen_random_bytes(16), 'hex'),
  -- Duplicate grouping (Phase 5)
  is_duplicate          boolean not null default false,
  duplicate_group_id    uuid,
  -- Contact info (never exposed to residents via public tracking endpoint)
  contact_email         text,
  contact_phone         text,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

-- Keep geom in sync with lat/lng via trigger
create or replace function sync_report_geom()
returns trigger language plpgsql as $$
begin
  new.geom := st_makepoint(new.longitude, new.latitude)::geography;
  new.updated_at := now();
  return new;
end;
$$;

create trigger trg_reports_geom
  before insert or update of latitude, longitude
  on reports
  for each row execute function sync_report_geom();

-- ─── Report Images ───────────────────────────────────────────────────────────
-- Keeps schema extensible; MVP submits one image but table supports multiple.

create table if not exists report_images (
  id           uuid primary key default gen_random_uuid(),
  report_id    uuid not null references reports(id) on delete cascade,
  storage_path text not null,
  public_url   text,
  created_at   timestamptz not null default now()
);

-- ─── AI Analysis ─────────────────────────────────────────────────────────────
-- One row per report, created by the AI pipeline (Phase 4).

create table if not exists ai_analysis (
  id                        uuid primary key default gen_random_uuid(),
  report_id                 uuid not null unique references reports(id) on delete cascade,
  ai_category               text,
  ai_severity               text,
  ai_department             text,
  ai_summary                text,
  recommended_action        text,
  resident_friendly_summary text,
  confidence_score          numeric(4,3),
  reasoning                 jsonb,
  created_at                timestamptz not null default now()
);

-- ─── Report Embeddings ───────────────────────────────────────────────────────
-- Stores vector embeddings for semantic duplicate detection (Phase 5).
-- Kept separate from ai_analysis for efficient ivfflat indexing.

create table if not exists report_embeddings (
  id         uuid primary key default gen_random_uuid(),
  report_id  uuid not null unique references reports(id) on delete cascade,
  -- 1536 dims matches text-embedding-3-small
  embedding  vector(1536),
  created_at timestamptz not null default now()
);

-- ─── Duplicate Suggestions ───────────────────────────────────────────────────
-- Candidate duplicate pairs surfaced for admin review (Phase 5).

create table if not exists duplicate_suggestions (
  id                  uuid primary key default gen_random_uuid(),
  report_id           uuid not null references reports(id) on delete cascade,
  candidate_report_id uuid not null references reports(id) on delete cascade,
  semantic_score      numeric(5,4),
  distance_meters     numeric(10,2),
  combined_score      numeric(5,4),
  confirmed           boolean not null default false,
  created_at          timestamptz not null default now(),
  unique (report_id, candidate_report_id)
);

-- ─── Status Events ───────────────────────────────────────────────────────────
-- Append-only audit log for all status transitions.

create table if not exists status_events (
  id          uuid primary key default gen_random_uuid(),
  report_id   uuid not null references reports(id) on delete cascade,
  old_status  text,
  new_status  text not null,
  note        text,
  public_note text,
  changed_by  uuid references profiles(id) on delete set null,
  created_at  timestamptz not null default now()
);

-- ─── Notifications ───────────────────────────────────────────────────────────
-- Outbound notification log for email and SMS (Phase 6).

create table if not exists notifications (
  id                uuid primary key default gen_random_uuid(),
  report_id         uuid not null references reports(id) on delete cascade,
  channel           text not null check (channel in ('email','sms')),
  recipient         text not null,
  subject           text,
  body              text,
  status            text not null default 'pending' check (status in ('pending','sent','failed')),
  provider_response jsonb,
  created_at        timestamptz not null default now(),
  sent_at           timestamptz
);

-- ─── Indexes ─────────────────────────────────────────────────────────────────

-- Geospatial index for radius queries and map display
create index if not exists idx_reports_geom
  on reports using gist (geom);

-- Common dashboard filter columns
create index if not exists idx_reports_status     on reports (status);
create index if not exists idx_reports_category   on reports (category);
create index if not exists idx_reports_severity   on reports (severity);
create index if not exists idx_reports_department on reports (department_id);
create index if not exists idx_reports_created    on reports (created_at desc);

-- Embedding similarity search (Phase 5 — build after initial data load)
-- create index idx_report_embeddings_vector
--   on report_embeddings using ivfflat (embedding vector_cosine_ops)
--   with (lists = 100);

-- Status event lookup by report
create index if not exists idx_status_events_report on status_events (report_id, created_at desc);

-- Notification lookup
create index if not exists idx_notifications_report on notifications (report_id);
