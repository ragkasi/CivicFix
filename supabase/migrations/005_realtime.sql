-- Phase 8: Supabase Realtime configuration.
-- Run after 004_duplicate_functions.sql.
--
-- REPLICA IDENTITY FULL ensures Realtime events include the full old row
-- data on UPDATE and DELETE operations, not just the primary key.
--
-- After running this migration:
--   1. Go to Supabase dashboard → Database → Replication
--   2. Enable replication for the `reports` table
--      (or use the SQL below if you prefer SQL-only setup)

-- ─── REPLICA IDENTITY FULL ───────────────────────────────────────────────────

alter table reports           replica identity full;
alter table status_events     replica identity full;
alter table ai_analysis       replica identity full;
alter table duplicate_suggestions replica identity full;

-- ─── Add tables to supabase_realtime publication ─────────────────────────────
-- The supabase_realtime publication exists on hosted Supabase projects.
-- This block handles environments where it may not exist yet.

do $$
begin
    -- reports (primary realtime table for the admin dashboard)
    begin
        alter publication supabase_realtime add table reports;
    exception when undefined_object then
        raise notice 'supabase_realtime publication not found — enable Realtime in Supabase dashboard';
    when duplicate_object then
        null; -- Table already in publication
    end;

    -- status_events (optional — useful for future realtime status updates)
    begin
        alter publication supabase_realtime add table status_events;
    exception when others then
        null;
    end;
end;
$$;
