-- Geospatial query functions for CivicFix.
-- Run after 002_schema.sql.
-- Requires: postgis extension.
-- Callable via Supabase client: client.rpc("function_name", params)

-- ─── Nearby reports ───────────────────────────────────────────────────────────
-- Returns reports within a given radius of a point, ordered by distance.

create or replace function nearby_reports(
    input_lat    double precision,
    input_lng    double precision,
    radius_meters double precision default 1000,
    result_limit  integer          default 50
)
returns table (
    id                    uuid,
    description           text,
    category              text,
    severity              text,
    status                text,
    latitude              double precision,
    longitude             double precision,
    address               text,
    department_id         uuid,
    public_tracking_token text,
    created_at            timestamptz,
    updated_at            timestamptz,
    distance_meters       double precision
)
language sql
stable
as $$
    select
        r.id,
        r.description,
        r.category,
        r.severity,
        r.status,
        r.latitude,
        r.longitude,
        r.address,
        r.department_id,
        r.public_tracking_token,
        r.created_at,
        r.updated_at,
        st_distance(
            r.geom,
            st_makepoint(input_lng, input_lat)::geography
        ) as distance_meters
    from reports r
    where
        r.geom is not null
        and st_dwithin(
            r.geom,
            st_makepoint(input_lng, input_lat)::geography,
            radius_meters
        )
    order by distance_meters asc
    limit result_limit;
$$;

-- ─── Reports in bounding box ──────────────────────────────────────────────────
-- Returns reports within a geographic bounding box.
-- bbox format: minLng, minLat, maxLng, maxLat

create or replace function reports_in_bbox(
    min_lng      double precision,
    min_lat      double precision,
    max_lng      double precision,
    max_lat      double precision,
    result_limit integer default 200
)
returns table (
    id                    uuid,
    description           text,
    category              text,
    severity              text,
    status                text,
    latitude              double precision,
    longitude             double precision,
    address               text,
    department_id         uuid,
    public_tracking_token text,
    created_at            timestamptz,
    updated_at            timestamptz
)
language sql
stable
as $$
    select
        r.id,
        r.description,
        r.category,
        r.severity,
        r.status,
        r.latitude,
        r.longitude,
        r.address,
        r.department_id,
        r.public_tracking_token,
        r.created_at,
        r.updated_at
    from reports r
    where
        r.geom is not null
        and st_within(
            r.geom::geometry,
            st_makeenvelope(min_lng, min_lat, max_lng, max_lat, 4326)
        )
    order by r.created_at desc
    limit result_limit;
$$;
