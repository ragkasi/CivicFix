"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type ReportDetail, type ReportCategory, type ReportSeverity, type ReportStatus } from "@/lib/api";
import { StatusBadge, SeverityBadge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";

const CATEGORY_LABELS: Record<string, string> = {
  pothole: "Pothole", streetlight: "Streetlight", flooding: "Flooding",
  sidewalk_damage: "Sidewalk", trash_overflow: "Trash", damaged_sign: "Sign",
  road_hazard: "Road Hazard", graffiti: "Graffiti", snow_or_ice: "Snow/Ice",
  other: "Other",
};

const PAGE_LIMIT = 20;

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

export default function AdminPage() {
  const [reports, setReports] = useState<ReportDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const [filterStatus, setFilterStatus] = useState<ReportStatus | "">("");
  const [filterCategory, setFilterCategory] = useState<ReportCategory | "">("");
  const [filterSeverity, setFilterSeverity] = useState<ReportSeverity | "">("");

  async function fetchReports(pg: number) {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {
        limit: String(PAGE_LIMIT),
        offset: String(pg * PAGE_LIMIT),
      };
      if (filterStatus) params.status = filterStatus;
      if (filterCategory) params.category = filterCategory;
      if (filterSeverity) params.severity = filterSeverity;

      const data = await api.reports.list(params);
      setReports(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setPage(0);
    fetchReports(0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterStatus, filterCategory, filterSeverity]);

  function handlePageChange(dir: -1 | 1) {
    const next = page + dir;
    setPage(next);
    fetchReports(next);
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-blue-600 hover:underline">
            ← Home
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-0.5">Admin Dashboard</h1>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/admin/map"
            className="text-sm font-medium text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
          >
            🗺️ Map View
          </Link>
          <Link
            href="/report/new"
            className="text-sm font-medium text-blue-600 border border-blue-200 px-3 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
          >
            + New Report
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-4">
        {/* Filters */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap gap-4">
          <div className="min-w-36">
            <Select
              label="Status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as ReportStatus | "")}
            >
              <option value="">All statuses</option>
              <option value="submitted">Submitted</option>
              <option value="reviewed">Reviewed</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="duplicate">Duplicate</option>
              <option value="rejected">Rejected</option>
            </Select>
          </div>
          <div className="min-w-36">
            <Select
              label="Category"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value as ReportCategory | "")}
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
              <option value="snow_or_ice">Snow / Ice</option>
              <option value="other">Other</option>
            </Select>
          </div>
          <div className="min-w-36">
            <Select
              label="Severity"
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value as ReportSeverity | "")}
            >
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </Select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => { setFilterStatus(""); setFilterCategory(""); setFilterSeverity(""); }}
              className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-50"
            >
              Clear filters
            </button>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span className="ml-3 text-sm text-gray-500">Loading reports…</span>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-sm text-red-700">
            {error}
            <button onClick={() => fetchReports(page)} className="ml-3 underline">
              Retry
            </button>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && reports.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-3">📋</div>
            <p className="font-medium text-gray-600">No reports found</p>
            <p className="text-sm mt-1">
              {filterStatus || filterCategory || filterSeverity
                ? "Try clearing the filters."
                : "Submit the first report at /report/new."}
            </p>
          </div>
        )}

        {/* Table */}
        {!loading && !error && reports.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Category</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Severity</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Address</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Department</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Submitted</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {reports.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {CATEGORY_LABELS[r.category ?? ""] ?? r.category ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <SeverityBadge severity={r.severity} />
                    </td>
                    <td className="px-4 py-3 text-gray-600 max-w-48 truncate">
                      {r.address ?? `${r.latitude.toFixed(4)}, ${r.longitude.toFixed(4)}`}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {r.department?.name ?? <span className="text-gray-400">Unassigned</span>}
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {formatDate(r.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/admin/reports/${r.id}`}
                        className="text-blue-600 hover:underline font-medium"
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
              <span className="text-sm text-gray-500">
                Page {page + 1} · showing {reports.length} report{reports.length !== 1 ? "s" : ""}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange(-1)}
                  disabled={page === 0}
                  className="text-sm px-3 py-1.5 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => handlePageChange(1)}
                  disabled={reports.length < PAGE_LIMIT}
                  className="text-sm px-3 py-1.5 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
