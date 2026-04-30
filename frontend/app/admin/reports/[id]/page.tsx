"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  api,
  type AIAnalysis,
  type Department,
  type DuplicateSuggestion,
  type NotificationResult,
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

const CATEGORY_LABELS_SMALL: Record<string, string> = {
  pothole: "Pothole", streetlight: "Streetlight", flooding: "Flooding",
  sidewalk_damage: "Sidewalk", trash_overflow: "Trash", damaged_sign: "Sign",
  road_hazard: "Road Hazard", graffiti: "Graffiti", snow_or_ice: "Snow/Ice", other: "Other",
};

function DuplicatesCard({ duplicates }: { duplicates: DuplicateSuggestion[] }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Possible Duplicates</CardTitle>
          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
            Admin review required
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {duplicates.length === 0 ? (
          <p className="text-sm text-gray-400">No likely duplicates found.</p>
        ) : (
          <ol className="space-y-3">
            {duplicates.map((d) => (
              <li
                key={d.candidate_report_id}
                className="border border-amber-100 bg-amber-50 rounded-lg px-4 py-3 text-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-gray-800 truncate max-w-xs">
                        {d.candidate_address ?? "No address"}
                      </span>
                      {d.candidate_category && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                          {CATEGORY_LABELS_SMALL[d.candidate_category] ?? d.candidate_category}
                        </span>
                      )}
                      {d.candidate_status && (
                        <span className="text-xs text-gray-500">{d.candidate_status}</span>
                      )}
                    </div>
                    {d.candidate_description && (
                      <p className="text-gray-500 text-xs line-clamp-2">{d.candidate_description}</p>
                    )}
                    <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
                      <span>Match: <strong>{Math.round(d.combined_score * 100)}%</strong></span>
                      <span>Semantic: {Math.round(d.semantic_score * 100)}%</span>
                      <span>Distance: {Math.round(d.distance_meters)} m</span>
                      {d.reason && <span className="italic">{d.reason}</span>}
                    </div>
                  </div>
                  <Link
                    href={`/admin/reports/${d.candidate_report_id}`}
                    className="text-blue-600 hover:underline text-xs whitespace-nowrap shrink-0"
                  >
                    View →
                  </Link>
                </div>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-700 bg-red-50",
  high: "text-orange-700 bg-orange-50",
  medium: "text-amber-700 bg-amber-50",
  low: "text-green-700 bg-green-50",
};

function AIAnalysisCard({ analysis }: { analysis: AIAnalysis | null }) {
  if (!analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg px-4 py-5 text-center text-sm text-gray-400">
            <p className="font-medium text-gray-500 mb-1">No AI analysis yet</p>
            <p>Click &ldquo;Analyse with AI&rdquo; to classify this report automatically.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>AI Analysis</CardTitle>
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">
            AI suggested — not confirmed
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Category</p>
            <p className="text-gray-800 font-medium">{CATEGORY_LABELS[analysis.ai_category ?? ""] ?? analysis.ai_category ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Severity</p>
            {analysis.ai_severity ? (
              <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[analysis.ai_severity] ?? "text-gray-700 bg-gray-100"}`}>
                {analysis.ai_severity}
              </span>
            ) : <span className="text-gray-400">—</span>}
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Suggested Dept</p>
            <p className="text-gray-800">{analysis.ai_department ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Confidence</p>
            <p className="text-gray-800">
              {analysis.confidence_score != null
                ? `${Math.round(analysis.confidence_score * 100)}%`
                : "—"}
            </p>
          </div>
        </div>

        {analysis.ai_summary && (
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Summary</p>
            <p className="text-gray-700 bg-gray-50 rounded-lg px-3 py-2">{analysis.ai_summary}</p>
          </div>
        )}

        {analysis.recommended_action && (
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Recommended Action</p>
            <p className="text-gray-700">{analysis.recommended_action}</p>
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-gray-400 pt-1 border-t border-gray-100">
          <span>Model: {analysis.reasoning?.model ?? "gpt-4o"}</span>
          <span>{fmt(analysis.created_at)}</span>
        </div>
      </CardContent>
    </Card>
  );
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

  // AI analysis state
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeMsg, setAnalyzeMsg] = useState<string | null>(null);

  // Duplicate detection state
  const [checkingDupes, setCheckingDupes] = useState(false);
  const [dupesMsg, setDupesMsg] = useState<string | null>(null);

  // Notify resident state
  const [notifying, setNotifying] = useState(false);
  const [notifyResults, setNotifyResults] = useState<NotificationResult[] | null>(null);
  const [notifyMsg, setNotifyMsg] = useState<string | null>(null);

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

  async function handleNotifyResident() {
    setNotifying(true);
    setNotifyResults(null);
    setNotifyMsg(null);
    try {
      const res = await api.reports.notify(id);
      setNotifyResults(res.results);
      if (res.count === 0) {
        setNotifyMsg("No contact info on file — no notification sent.");
      } else {
        setNotifyMsg(`${res.count} notification${res.count !== 1 ? "s" : ""} processed.`);
      }
    } catch (e) {
      setNotifyMsg(e instanceof Error ? e.message : "Notification failed");
    } finally {
      setNotifying(false);
    }
  }

  async function handleCheckDuplicates() {
    setCheckingDupes(true);
    setDupesMsg(null);
    try {
      await api.reports.findDuplicates(id);
      await loadReport();
      setDupesMsg("Duplicate check complete.");
    } catch (e) {
      setDupesMsg(e instanceof Error ? e.message : "Duplicate check failed");
    } finally {
      setCheckingDupes(false);
    }
  }

  async function handleAnalyze() {
    setAnalyzing(true);
    setAnalyzeMsg(null);
    try {
      await api.reports.analyze(id);
      await loadReport(); // Refresh to pick up updated category/severity + ai_analysis
      setAnalyzeMsg("AI analysis complete.");
    } catch (e) {
      setAnalyzeMsg(e instanceof Error ? e.message : "AI analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

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

          {/* AI Analysis panel */}
          <AIAnalysisCard analysis={report.ai_analysis} />

          {/* Duplicate suggestions */}
          <DuplicatesCard duplicates={report.duplicate_suggestions} />

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

          {/* Analyze with AI */}
          <Card>
            <CardHeader><CardTitle>AI Triage</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-gray-500">
                Run AI classification to auto-fill category, severity, and department suggestion.
              </p>
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="w-full py-2 text-sm font-semibold text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
              >
                {analyzing ? "Analysing…" : "Analyse with AI"}
              </button>
              {analyzeMsg && (
                <p className={`text-sm text-center ${analyzeMsg.includes("complete") ? "text-green-600" : "text-red-600"}`}>
                  {analyzeMsg}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Notify Resident */}
          <Card>
            <CardHeader><CardTitle>Notify Resident</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-gray-500">
                Send a status update to the resident via email/SMS if contact info is on file.
              </p>
              <button
                onClick={handleNotifyResident}
                disabled={notifying}
                className="w-full py-2 text-sm font-semibold text-white bg-teal-600 rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors"
              >
                {notifying ? "Sending…" : "Notify Resident"}
              </button>
              {notifyMsg && (
                <p className={`text-sm text-center ${notifyMsg.includes("No contact") ? "text-gray-500" : notifyMsg.includes("failed") || notifyMsg.includes("Failed") ? "text-red-600" : "text-green-600"}`}>
                  {notifyMsg}
                </p>
              )}
              {notifyResults && notifyResults.length > 0 && (
                <ul className="text-xs space-y-1">
                  {notifyResults.map((r, i) => (
                    <li key={i} className={`flex items-center gap-2 ${r.status === "failed" ? "text-red-600" : "text-gray-600"}`}>
                      <span>{r.channel === "email" ? "📧" : "📱"}</span>
                      <span className="capitalize">{r.channel}</span>
                      <span>·</span>
                      <span>{r.status}{r.is_mock ? " (mock)" : ""}</span>
                      {r.error && <span className="text-red-500">— {r.error}</span>}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          {/* Check for Duplicates */}
          <Card>
            <CardHeader><CardTitle>Duplicate Detection</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-gray-500">
                Find similar nearby reports using semantic embeddings and geolocation.
                Requires AI analysis to have run first.
              </p>
              <button
                onClick={handleCheckDuplicates}
                disabled={checkingDupes}
                className="w-full py-2 text-sm font-semibold text-white bg-amber-600 rounded-lg hover:bg-amber-700 disabled:opacity-50 transition-colors"
              >
                {checkingDupes ? "Checking…" : "Check for Duplicates"}
              </button>
              {dupesMsg && (
                <p className={`text-sm text-center ${dupesMsg.includes("complete") ? "text-green-600" : "text-red-600"}`}>
                  {dupesMsg}
                </p>
              )}
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
