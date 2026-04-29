import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="space-y-3">
          <span className="inline-block bg-blue-100 text-blue-700 text-sm font-medium px-3 py-1 rounded-full">
            Civic Tech Platform
          </span>
          <h1 className="text-5xl font-bold text-gray-900 tracking-tight">
            CivicFix
          </h1>
          <p className="text-xl text-gray-600 max-w-lg mx-auto leading-relaxed">
            Report local infrastructure issues — potholes, flooding, broken
            streetlights, and more. AI routes your report to the right city
            department automatically.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/report/new"
            className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Report an Issue
          </Link>
          <Link
            href="/admin"
            className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Admin Dashboard
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 text-left">
          {[
            {
              icon: "📍",
              title: "Submit with Location",
              desc: "Drop a pin or use GPS to show exactly where the issue is.",
            },
            {
              icon: "🤖",
              title: "AI Triage",
              desc: "AI classifies severity and routes the report to the right department.",
            },
            {
              icon: "📊",
              title: "Track Progress",
              desc: "Get status updates as your report moves through resolution.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="bg-white p-5 rounded-xl border border-gray-200"
            >
              <div className="text-2xl mb-2">{item.icon}</div>
              <h3 className="font-semibold text-gray-900">{item.title}</h3>
              <p className="text-sm text-gray-500 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
