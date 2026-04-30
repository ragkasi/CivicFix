"use client";

import { useEffect, useRef, useState } from "react";
import { supabaseClient } from "@/lib/supabase";

export type RealtimeStatus =
  | "connecting"
  | "connected"
  | "disconnected"
  | "unavailable";

export interface UseRealtimeReportsOptions {
  onInsert?: (row: Record<string, unknown>) => void;
  onUpdate?: (row: Record<string, unknown>) => void;
  onDelete?: (row: Record<string, unknown>) => void;
}

/**
 * Subscribe to Supabase Realtime changes on the reports table.
 *
 * Callbacks are stored in refs so the subscription does not restart when
 * the parent re-renders with new inline function references.
 *
 * Returns `status: "unavailable"` when NEXT_PUBLIC_SUPABASE_URL or
 * NEXT_PUBLIC_SUPABASE_ANON_KEY are not set — the rest of the app continues
 * to work normally in that case.
 *
 * Requires:
 *   - supabase/migrations/005_realtime.sql applied
 *   - reports table enabled in the supabase_realtime publication
 */
export function useRealtimeReports({
  onInsert,
  onUpdate,
  onDelete,
}: UseRealtimeReportsOptions = {}) {
  const [status, setStatus] = useState<RealtimeStatus>(
    supabaseClient ? "connecting" : "unavailable"
  );

  // Stable callback refs — updated each render but subscription is created once
  const onInsertRef = useRef(onInsert);
  const onUpdateRef = useRef(onUpdate);
  const onDeleteRef = useRef(onDelete);

  useEffect(() => { onInsertRef.current = onInsert; }, [onInsert]);
  useEffect(() => { onUpdateRef.current = onUpdate; }, [onUpdate]);
  useEffect(() => { onDeleteRef.current = onDelete; }, [onDelete]);

  useEffect(() => {
    if (!supabaseClient) return;
    // Capture in a local const so the cleanup closure has a non-null reference
    const client = supabaseClient;

    const channel = client
      .channel("civicfix-reports-admin")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "reports" },
        (payload) =>
          onInsertRef.current?.(payload.new as Record<string, unknown>)
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "reports" },
        (payload) =>
          onUpdateRef.current?.(payload.new as Record<string, unknown>)
      )
      .on(
        "postgres_changes",
        { event: "DELETE", schema: "public", table: "reports" },
        (payload) =>
          onDeleteRef.current?.(payload.old as Record<string, unknown>)
      )
      .subscribe((subscriptionStatus) => {
        switch (subscriptionStatus) {
          case "SUBSCRIBED":
            setStatus("connected");
            break;
          case "CHANNEL_ERROR":
          case "TIMED_OUT":
          case "CLOSED":
            setStatus("disconnected");
            break;
          default:
            setStatus("connecting");
        }
      });

    return () => {
      client.removeChannel(channel);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps — intentionally runs once

  return { status };
}
