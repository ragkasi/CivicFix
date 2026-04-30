import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

/**
 * Browser Supabase client (anon key only — never use service role key here).
 * Null when env vars are not configured; callers must handle this.
 */
export const supabaseClient: SupabaseClient | null =
  url && anonKey ? createClient(url, anonKey) : null;
