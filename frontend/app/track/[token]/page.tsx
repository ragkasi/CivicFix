"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type TrackingReport } from "@/lib/api";
import { StatusBadge, SeverityBadge } from "@/components/ui/badge";

const CATEGORY_LABELS: Record<string, string> = {
  pothole:        "Pothole / Road Damage",
  streetlight:    "Broken Streetlight",
  flooding:       "Drainage / Flooding",
  sidewalk_damage:"Sidewalk Damage",
  trash_overflow: "Trash Overflow",
  damaged_sign:   "Damaged Sign",
  road_hazard:    "Road Hazard",
  graffiti:       "Graffiti",
  snow_or_ice:    "Snow / Ice Hazard",
  other:          "Other",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function TrackPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;

  const [report, setReport] = useState<TrackingReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    api.tracking
      .get(token)
      .then((data) => setReport(data))
      .catch((err: Error) => {
        if (err.message.includes("404")) {
          setNotFound(true);
        } else {
          setError("Unable to load report status. Please try again later.");
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-gray-500">Loading report status…</p>
        </div>
      </main>
    );
  }

  // ── Not found ────────────────────────────────────────────────────────────
  if (notFound) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md text-center space-y-4">
          <div className="text-5xl">🔍</div>
          <h1 className="text-2xl font-bold text-gray-900">Report not found</h1>
          <p className="text-gray-500">
            The tracking link you followed doesn&apos;t match any report. Check
            that you copied the full URL.
          </p>
          <Link
            href="/report/new"
            className="inline-flex items-center px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Submit a new report
          </Link>
        </div>
      </main>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────
  if (error || !report) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md text-center space-y-4">
          <div className="text-5xl">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900">
            Something went wrong
          </h1>
          <p className="text-gray-500">{error ?? "Please try again later."}</p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </main>
    );
  }

  // ── Report found ─────────────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <Link
            href="/"
            className="text-sm text-blue-600 hover:underline mb-4 inline-block"
          >
            &larr; Back to home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Report Status</h1>
          <p className="text-gray-500 text-sm mt-1">
            Tracking ID:{" "}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">
              {report.tracking_token}
            </code>
          </p>
        </div>

        {/* Status card */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
          {/* Status + severity */}
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={report.status} className="text-sm px-3 py-1" />
            {report.severity && (
              <SeverityBadge
                severity={report.severity}
                className="text-sm px-3 py-1"
              />
            )}
          </div>

          <hr className="border-gray-100" />

          {/* Details grid */}
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {report.category && (
              <div>
                <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                  Category
                </dt>
                <dd className="text-sm text-gray-900 mt-0.5">
                  {CATEGORY_LABELS[report.category] ?? report.category}
                </dd>
              </div>
            )}

            {report.address && (
              <div>
                <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                  Location
                </dt>
                <dd className="text-sm text-gray-900 mt-0.5">
                  {report.address}
                </dd>
              </div>
            )}

            <div>
              <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Submitted
              </dt>
              <dd className="text-sm text-gray-900 mt-0.5">
                {formatDate(report.created_at)}
              </dd>
            </div>

            {report.updated_at && (
              <div>
                <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                  Last updated
                </dt>
                <dd className="text-sm text-gray-900 mt-0.5">
                  {formatDate(report.updated_at)}
                </dd>
              </div>
            )}
          </dl>

          {/* Public note */}
          {report.public_note && (
            <>
              <hr className="border-gray-100" />
              <div>
                <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
                  Update from the city
                </dt>
                <p className="text-sm text-gray-700 bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
                  {report.public_note}
                </p>
              </div>
            </>
          )}
        </div>

        {/* Status explanation */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">
            What happens next?
          </h2>
          <ol className="space-y-2 text-sm text-gray-600">
            {[
              ["Submitted",   "Your report has been received and is queued for review."],
              ["Reviewed",    "City staff has reviewed the report details."],
              ["Assigned",    "The report has been assigned to a department."],
              ["In Progress", "A crew or team is actively working on it."],
              ["Resolved",    "The issue has been addressed."],
            ].map(([step, desc]) => (
              <li key={step} className="flex items-start gap-2">
                <span className="font-medium text-gray-800 w-24 shrink-0">
                  {step}
                </span>
                <span>{desc}</span>
              </li>
            ))}
          </ol>
        </div>

        <p className="text-xs text-center text-gray-400">
          Bookmark this page to check back on your report.
        </p>
      </div>
    </main>
  );
}
