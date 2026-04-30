"use client";

import { useEffect, useRef, useState } from "react";
import { supabaseClient } from "@/lib/supabase";
import type { RealtimeStatus } from "@/hooks/useRealtimeReports";

/**
 * Subscribe to Supabase Realtime updates for a specific resident report
 * using the public_tracking_token as the filter key.
 *
 * Privacy design:
 *   - Subscribes to the `reports` table, not `status_events`
 *   - Filters by `public_tracking_token` — the same identifier the resident holds
 *   - Does NOT use the realtime payload content (which could contain private fields)
 *   - Calls `onUpdate()` to trigger a re-fetch of the safe tracking API endpoint
 *
 * Degrades to "unavailable" when NEXT_PUBLIC_SUPABASE_URL or
 * NEXT_PUBLIC_SUPABASE_ANON_KEY are not set.
 */
export function useRealtimeTracking(
  token: string,
  onUpdate: () => void
): { status: RealtimeStatus } {
  const [status, setStatus] = useState<RealtimeStatus>(
    supabaseClient ? "connecting" : "unavailable"
  );

  const onUpdateRef = useRef(onUpdate);
  useEffect(() => { onUpdateRef.current = onUpdate; }, [onUpdate]);

  useEffect(() => {
    if (!supabaseClient || !token) return;
    const client = supabaseClient;

    const channel = client
      .channel(`civicfix-tracking-${token}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "reports",
          filter: `public_tracking_token=eq.${token}`,
        },
        () => {
          // Trigger a safe refetch — payload is intentionally ignored
          // to avoid accidentally displaying private report fields
          onUpdateRef.current();
        }
      )
      .subscribe((s) => {
        if (s === "SUBSCRIBED") setStatus("connected");
        else if (s === "CLOSED" || s === "CHANNEL_ERROR" || s === "TIMED_OUT")
          setStatus("disconnected");
        else setStatus("connecting");
      });

    return () => {
      client.removeChannel(channel);
    };
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  return { status };
}
