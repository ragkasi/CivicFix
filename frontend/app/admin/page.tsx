export default function AdminPage() {
  const features = [
    {
      title: "Report Map",
      desc: "Mapbox map with clustered pins, filtered by category, severity, and status.",
      phase: "Phase 3",
    },
    {
      title: "Report Table",
      desc: "Sortable, filterable list of submitted reports with bulk actions.",
      phase: "Phase 3",
    },
    {
      title: "AI Summary Panel",
      desc: "Per-report AI classification, severity score, department recommendation, and duplicate suggestions.",
      phase: "Phase 4",
    },
    {
      title: "Status Workflow",
      desc: "Update report status: Submitted → Reviewed → Assigned → In Progress → Resolved.",
      phase: "Phase 3",
    },
    {
      title: "Department Routing",
      desc: "AI-assisted and admin-overridable department assignment.",
      phase: "Phase 4",
    },
    {
      title: "Duplicate Detection",
      desc: "Embedding-based and geospatial duplicate suggestions across open reports.",
      phase: "Phase 5",
    },
  ];

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <span className="text-sm font-medium text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
            Phase 1 — Placeholder
          </span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Admin Dashboard
        </h1>
        <p className="text-gray-500 mb-8">
          The admin dashboard is built incrementally across Phases 3–5.
        </p>
        <div className="grid gap-3">
          {features.map((item) => (
            <div
              key={item.title}
              className="bg-white border border-gray-200 rounded-xl p-5 flex items-start justify-between gap-4"
            >
              <div>
                <h3 className="font-semibold text-gray-900">{item.title}</h3>
                <p className="text-sm text-gray-500 mt-1">{item.desc}</p>
              </div>
              <span className="text-xs text-gray-400 font-medium whitespace-nowrap pt-0.5">
                {item.phase}
              </span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
