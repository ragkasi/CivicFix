import { cn } from "@/lib/utils";
import type { ReportSeverity, ReportStatus } from "@/lib/api";

// ─── Status badge ─────────────────────────────────────────────────────────────

const STATUS_STYLES: Record<ReportStatus, string> = {
  submitted:   "bg-gray-100 text-gray-700 border-gray-200",
  reviewed:    "bg-blue-100 text-blue-700 border-blue-200",
  assigned:    "bg-indigo-100 text-indigo-700 border-indigo-200",
  in_progress: "bg-amber-100 text-amber-700 border-amber-200",
  resolved:    "bg-green-100 text-green-700 border-green-200",
  duplicate:   "bg-purple-100 text-purple-700 border-purple-200",
  rejected:    "bg-red-100 text-red-700 border-red-200",
};

const STATUS_LABELS: Record<ReportStatus, string> = {
  submitted:   "Submitted",
  reviewed:    "Reviewed",
  assigned:    "Assigned",
  in_progress: "In Progress",
  resolved:    "Resolved",
  duplicate:   "Duplicate",
  rejected:    "Rejected",
};

export function StatusBadge({
  status,
  className,
}: {
  status: ReportStatus;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
        STATUS_STYLES[status] ?? "bg-gray-100 text-gray-700 border-gray-200",
        className
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

// ─── Severity badge ───────────────────────────────────────────────────────────

const SEVERITY_STYLES: Record<ReportSeverity, string> = {
  low:      "bg-green-100 text-green-700 border-green-200",
  medium:   "bg-amber-100 text-amber-700 border-amber-200",
  high:     "bg-orange-100 text-orange-700 border-orange-200",
  critical: "bg-red-100 text-red-700 border-red-200",
};

const SEVERITY_LABELS: Record<ReportSeverity, string> = {
  low:      "Low",
  medium:   "Medium",
  high:     "High",
  critical: "Critical",
};

export function SeverityBadge({
  severity,
  className,
}: {
  severity: ReportSeverity | null | undefined;
  className?: string;
}) {
  if (!severity) {
    return (
      <span
        className={cn(
          "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
          "bg-gray-50 text-gray-400 border-gray-200",
          className
        )}
      >
        Pending
      </span>
    );
  }
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
        SEVERITY_STYLES[severity] ?? "bg-gray-100 text-gray-700 border-gray-200",
        className
      )}
    >
      {SEVERITY_LABELS[severity] ?? severity}
    </span>
  );
}
