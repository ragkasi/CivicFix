export default function NewReportPage() {
  const fields = [
    "Photo upload (image of the issue)",
    "Text description — what you see and where",
    "Optional voice input, transcribed automatically",
    "Map pin or GPS location capture",
    "Optional contact email or phone for status updates",
  ];

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <span className="text-sm font-medium text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
            Phase 1 — Placeholder
          </span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Report an Issue
        </h1>
        <p className="text-gray-500 mb-8">
          The resident report form is implemented in Phase 3.
        </p>
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="font-semibold text-gray-800 mb-4">
            Planned form fields
          </h2>
          <ul className="space-y-3">
            {fields.map((field) => (
              <li key={field} className="flex items-start gap-3 text-sm text-gray-600">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                {field}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  );
}
