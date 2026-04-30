"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  api,
  type ReportCategory,
  type ReportDetail,
  type ReportSeverity,
  type ReportStatus,
} from "@/lib/api";
import { Select } from "@/components/ui/select";

// SSR-safe dynamic import — Mapbox uses browser APIs
const ReportMap = dynamic(() => import("@/components/map/ReportMap"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gray-100">
      <p className="text-sm text-gray-500">Initialising map…</p>
    </div>
  ),
});

export default function AdminMapPage() {
  const [reports, setReports] = useState<ReportDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filterStatus, setFilterStatus] = useState<ReportStatus | "">("");
  const [filterCategory, setFilterCategory] = useState<ReportCategory | "">("");
  const [filterSeverity, setFilterSeverity] = useState<ReportSeverity | "">("");

  async function fetchReports() {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { limit: "500" };
      if (filterStatus) params.status = filterStatus;
      if (filterCategory) params.category = filterCategory;
      if (filterSeverity) params.severity = filterSeverity;
      setReports(await api.reports.list(params));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchReports();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterStatus, filterCategory, filterSeverity]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6 flex-shrink-0">
        <div>
          <Link href="/admin" className="text-sm text-blue-600 hover:underline">
            ← Table View
          </Link>
          <h1 className="text-lg font-bold text-gray-900 mt-0.5">Report Map</h1>
        </div>

        {/* Filters */}
        <div className="flex items-end gap-3 ml-4">
          <Select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as ReportStatus | "")}
            className="text-xs py-1.5 min-w-32"
          >
            <option value="">All statuses</option>
            <option value="submitted">Submitted</option>
            <option value="reviewed">Reviewed</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </Select>
          <Select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value as ReportCategory | "")}
            className="text-xs py-1.5 min-w-32"
          >
            <option value="">All categories</option>
            <option value="pothole">Pothole</option>
            <option value="streetlight">Streetlight</option>
            <option value="flooding">Flooding</option>
            <option value="sidewalk_damage">Sidewalk</option>
            <option value="trash_overflow">Trash</option>
            <option value="damaged_sign">Damaged Sign</option>
            <option value="road_hazard">Road Hazard</option>
            <option value="graffiti">Graffiti</option>
            <option value="snow_or_ice">Snow/Ice</option>
            <option value="other">Other</option>
          </Select>
          <Select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value as ReportSeverity | "")}
            className="text-xs py-1.5 min-w-28"
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
        </div>

        <div className="ml-auto text-sm text-gray-400">
          {!loading && `${reports.length} report${reports.length !== 1 ? "s" : ""}`}
        </div>
      </div>

      {/* Pin legend */}
      <div className="bg-white border-b border-gray-100 px-6 py-2 flex items-center gap-5 text-xs text-gray-500 flex-shrink-0">
        <span className="font-medium text-gray-600">Severity:</span>
        {[
          { label: "Critical", color: "#ef4444" },
          { label: "High", color: "#f97316" },
          { label: "Medium", color: "#f59e0b" },
          { label: "Low", color: "#22c55e" },
          { label: "Pending", color: "#6b7280" },
        ].map(({ label, color }) => (
          <span key={label} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-full inline-block"
              style={{ backgroundColor: color }}
            />
            {label}
          </span>
        ))}
      </div>

      {/* Map area */}
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-gray-500">Loading reports…</span>
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
            <div className="text-center">
              <p className="text-red-600 mb-2">{error}</p>
              <button
                onClick={fetchReports}
                className="text-sm text-blue-600 hover:underline"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {!loading && !error && reports.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
            <div className="text-center text-gray-400">
              <div className="text-4xl mb-2">🗺️</div>
              <p>No reports to display. Try clearing filters.</p>
            </div>
          </div>
        )}

        <ReportMap reports={reports} height="100%" />
      </div>
    </div>
  );
}
