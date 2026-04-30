-- Phase 7: Duplicate detection support.
-- Run after 003_geospatial_functions.sql.
-- Requires: pgvector, postgis.

-- ─── Add reason column to duplicate_suggestions ───────────────────────────────
-- Safe to run on an existing table (uses IF NOT EXISTS via DO block).

do $$
begin
    if not exists (
        select 1 from information_schema.columns
        where table_schema = 'public'
          and table_name   = 'duplicate_suggestions'
          and column_name  = 'reason'
    ) then
        alter table duplicate_suggestions add column reason text;
    end if;
end;
$$;

-- ─── find_duplicate_candidates ────────────────────────────────────────────────
-- Finds reports that are semantically similar (pgvector cosine distance) and
-- geographically nearby (PostGIS ST_DWithin) to a given source report.
--
-- Parameters:
--   source_report_id  UUID of the report to find duplicates for
--   radius_meters     maximum search radius (default 500 m)
--   result_limit      maximum candidates to return (pre-filtering)
--
-- Returns no rows when:
--   - source report does not exist
--   - source report has no embedding in report_embeddings
--   - source report has no geom (geom is set by trigger from lat/lng)
--
-- Callable via Supabase client:
--   client.rpc("find_duplicate_candidates", {...}).execute()

create or replace function find_duplicate_candidates(
    source_report_id uuid,
    radius_meters     float   default 500,
    result_limit      integer default 10
)
returns table (
    candidate_report_id  uuid,
    candidate_description text,
    candidate_category   text,
    candidate_severity   text,
    candidate_status     text,
    candidate_address    text,
    candidate_created_at timestamptz,
    cosine_distance      float,
    semantic_score       float,
    distance_meters      float
)
language sql
stable
as $$
    with source as (
        select
            r.id,
            r.geom,
            e.embedding
        from reports r
        join report_embeddings e on e.report_id = r.id
        where r.id = source_report_id
          and r.geom is not null
        limit 1
    )
    select
        r.id                                                  as candidate_report_id,
        r.description                                         as candidate_description,
        r.category                                            as candidate_category,
        r.severity                                            as candidate_severity,
        r.status                                              as candidate_status,
        r.address                                             as candidate_address,
        r.created_at                                          as candidate_created_at,
        (e.embedding <=> source.embedding)                    as cosine_distance,
        1.0 - (e.embedding <=> source.embedding)              as semantic_score,
        st_distance(r.geom, source.geom)                     as distance_meters
    from reports r
    join report_embeddings e on e.report_id = r.id
    cross join source
    where r.id != source_report_id
      and r.geom is not null
      and st_dwithin(r.geom, source.geom, radius_meters)
    order by (e.embedding <=> source.embedding) asc
    limit result_limit;
$$;
