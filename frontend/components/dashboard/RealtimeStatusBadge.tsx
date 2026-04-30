import { cn } from "@/lib/utils";
import type { RealtimeStatus } from "@/hooks/useRealtimeReports";

const STYLES: Record<RealtimeStatus, string> = {
  connected:   "bg-green-100 text-green-700",
  connecting:  "bg-amber-100 text-amber-700 animate-pulse",
  disconnected: "bg-red-100 text-red-700",
  unavailable:  "bg-gray-100 text-gray-500",
};

const LABELS: Record<RealtimeStatus, string> = {
  connected:   "● Live",
  connecting:  "◌ Connecting",
  disconnected: "○ Offline",
  unavailable:  "Realtime off",
};

const TITLES: Record<RealtimeStatus, string> = {
  connected:   "Supabase Realtime connected — dashboard updates automatically",
  connecting:  "Connecting to Supabase Realtime…",
  disconnected: "Supabase Realtime disconnected — refresh manually to see new data",
  unavailable:  "Supabase Realtime unavailable — set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY",
};

export function RealtimeStatusBadge({
  status,
  className,
}: {
  status: RealtimeStatus;
  className?: string;
}) {
  return (
    <span
      title={TITLES[status]}
      className={cn(
        "inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full select-none",
        STYLES[status],
        className
      )}
    >
      {LABELS[status]}
    </span>
  );
}
