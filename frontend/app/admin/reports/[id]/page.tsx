"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  api,
  type Department,
  type ReportDetail,
  type ReportStatus,
} from "@/lib/api";
import { StatusBadge, SeverityBadge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const CATEGORY_LABELS: Record<string, string> = {
  pothole: "Pothole / Road Damage", streetlight: "Broken Streetlight",
  flooding: "Drainage / Flooding", sidewalk_damage: "Sidewalk Damage",
  trash_overflow: "Trash Overflow", damaged_sign: "Damaged Sign",
  road_hazard: "Road Hazard", graffiti: "Graffiti",
  snow_or_ice: "Snow / Ice Hazard", other: "Other",
};

function fmt(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();

  const [report, setReport] = useState<ReportDetail | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Status form state
  const [newStatus, setNewStatus] = useState<ReportStatus>("reviewed");
  const [publicNote, setPublicNote] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);

  // Department form state
  const [selectedDept, setSelectedDept] = useState("");
  const [deptMsg, setDeptMsg] = useState<string | null>(null);
  const [deptLoading, setDeptLoading] = useState(false);

  async function loadReport() {
    try {
      const r = await api.reports.get(id);
      setReport(r);
      setNewStatus(r.status);
      setSelectedDept(r.department_id ?? "");
    } catch (e: unknown) {
      if (e instanceof Error && e.message.includes("404")) {
        setNotFound(true);
      } else {
        setError(e instanceof Error ? e.message : "Failed to load report");
      }
    }
  }

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      loadReport(),
      api.departments.list().then(setDepartments).catch(() => {}),
    ]).finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleStatusUpdate(e: React.FormEvent) {
    e.preventDefault();
    setStatusLoading(true);
    setStatusMsg(null);
    try {
      const updated = await api.reports.updateStatus(id, {
        status: newStatus,
        public_note: publicNote.trim() || undefined,
      });
      setReport(updated);
      setPublicNote("");
      setStatusMsg("Status updated successfully.");
    } catch (e) {
      setStatusMsg(e instanceof Error ? e.message : "Failed to update status");
    } finally {
      setStatusLoading(false);
    }
  }

  async function handleDeptAssign(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDept) return;
    setDeptLoading(true);
    setDeptMsg(null);
    try {
      const updated = await api.reports.assignDepartment(id, {
        department_id: selectedDept,
      });
      setReport(updated);
      setDeptMsg("Department assigned successfully.");
    } catch (e) {
      setDeptMsg(e instanceof Error ? e.message : "Failed to assign department");
    } finally {
      setDeptLoading(false);
    }
  }

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </main>
    );
  }

  if (notFound) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="text-4xl">🔍</div>
          <p className="font-semibold text-gray-800">Report not found</p>
          <Link href="/admin" className="text-sm text-blue-600 hover:underline">
            ← Back to dashboard
          </Link>
        </div>
      </main>
    );
  }

  if (error || !report) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-red-600">{error ?? "Something went wrong"}</p>
          <button onClick={() => { setError(null); setLoading(true); loadReport().finally(() => setLoading(false)); }}
            className="text-sm text-blue-600 hover:underline">Retry</button>
        </div>
      </main>
    );
  }

  // ── Full detail ──────────────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-gray-50 pb-12">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <Link href="/admin" className="text-sm text-blue-600 hover:underline">
          ← Admin Dashboard
        </Link>
        <div className="flex items-center gap-3 mt-1">
          <h1 className="text-2xl font-bold text-gray-900">Report Detail</h1>
          <StatusBadge status={report.status} />
          <SeverityBadge severity={report.severity} />
        </div>
        <p className="text-xs text-gray-400 mt-0.5 font-mono">{report.id}</p>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left column */}
        <div className="lg:col-span-2 space-y-4">

          {/* Report info */}
          <Card>
            <CardHeader><CardTitle>Report Details</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Description</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{report.description}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Category</p>
                  <p className="text-gray-800">{CATEGORY_LABELS[report.category ?? ""] ?? report.category ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Department</p>
                  <p className="text-gray-800">{report.department?.name ?? <span className="text-gray-400">Unassigned</span>}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Address</p>
                  <p className="text-gray-800">{report.address ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Coordinates</p>
                  <p className="text-gray-800 font-mono text-xs">{report.latitude}, {report.longitude}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Submitted</p>
                  <p className="text-gray-800">{fmt(report.created_at)}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Last Updated</p>
                  <p className="text-gray-800">{fmt(report.updated_at)}</p>
                </div>
              </div>

              {/* Image */}
              {report.images.length > 0 && report.images[0].public_url && (
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Photo</p>
                  <Image
                    src={report.images[0].public_url}
                    alt="Report photo"
                    width={600}
                    height={300}
                    className="w-full max-h-64 object-cover rounded-lg border border-gray-200"
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Analysis placeholder */}
          <Card>
            <CardHeader><CardTitle>AI Analysis</CardTitle></CardHeader>
            <CardContent>
              <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg px-4 py-6 text-center text-sm text-gray-400">
                <p className="font-medium text-gray-500 mb-1">Pending AI Analysis</p>
                <p>AI classification, severity scoring, and department routing will appear here in Phase 5.</p>
              </div>
            </CardContent>
          </Card>

          {/* Status history */}
          <Card>
            <CardHeader><CardTitle>Status History</CardTitle></CardHeader>
            <CardContent>
              {report.status_events.length === 0 ? (
                <p className="text-sm text-gray-400">No status changes yet.</p>
              ) : (
                <ol className="space-y-3">
                  {report.status_events.map((ev) => (
                    <li key={ev.id} className="flex gap-3 text-sm">
                      <div className="flex flex-col items-center">
                        <span className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                        <span className="flex-1 w-px bg-gray-200 mt-1" />
                      </div>
                      <div className="pb-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          {ev.old_status && (
                            <><span className="text-gray-400">{ev.old_status}</span><span className="text-gray-400">→</span></>
                          )}
                          <span className="font-medium text-gray-800">{ev.new_status}</span>
                          <span className="text-gray-400 text-xs">{fmt(ev.created_at)}</span>
                        </div>
                        {ev.public_note && (
                          <p className="text-gray-600 mt-0.5">{ev.public_note}</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column — admin actions */}
        <div className="space-y-4">

          {/* Update status */}
          <Card>
            <CardHeader><CardTitle>Update Status</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={handleStatusUpdate} className="space-y-3">
                <Select
                  label="New status"
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value as ReportStatus)}
                >
                  <option value="submitted">Submitted</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="duplicate">Duplicate</option>
                  <option value="rejected">Rejected</option>
                </Select>
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">
                    Public note (optional)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Message visible to the resident..."
                    value={publicNote}
                    onChange={(e) => setPublicNote(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={statusLoading}
                  className="w-full py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {statusLoading ? "Updating…" : "Update Status"}
                </button>
                {statusMsg && (
                  <p className={`text-sm text-center ${statusMsg.includes("success") ? "text-green-600" : "text-red-600"}`}>
                    {statusMsg}
                  </p>
                )}
              </form>
            </CardContent>
          </Card>

          {/* Assign department */}
          <Card>
            <CardHeader><CardTitle>Assign Department</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={handleDeptAssign} className="space-y-3">
                <Select
                  label="Department"
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value)}
                  disabled={departments.length === 0}
                >
                  <option value="">Select a department…</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </Select>
                <button
                  type="submit"
                  disabled={!selectedDept || deptLoading}
                  className="w-full py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {deptLoading ? "Assigning…" : "Assign Department"}
                </button>
                {deptMsg && (
                  <p className={`text-sm text-center ${deptMsg.includes("success") ? "text-green-600" : "text-red-600"}`}>
                    {deptMsg}
                  </p>
                )}
              </form>
            </CardContent>
          </Card>

          {/* Tracking link */}
          <Card>
            <CardHeader><CardTitle>Resident Tracking</CardTitle></CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500 mb-2">Public tracking link for this report:</p>
              <Link
                href={`/track/${report.tracking_token}`}
                target="_blank"
                className="text-xs text-blue-600 hover:underline break-all font-mono"
              >
                /track/{report.tracking_token}
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
