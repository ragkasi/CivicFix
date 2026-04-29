const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchApi<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }

  return res.json() as Promise<T>;
}

// ─── System ──────────────────────────────────────────────────────────────────

export const api = {
  health: () => fetchApi<{ status: string; version: string }>("/health"),

  // ─── Reports ─────────────────────────────────────────────────────────────
  reports: {
    /** Phase 3: submit a new report */
    create: (body: CreateReportBody) =>
      fetchApi<ReportResponse>("/api/reports", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** Phase 3: list reports with optional filters */
    list: (params?: Partial<ListReportsParams>) => {
      const qs = params
        ? "?" + new URLSearchParams(params as Record<string, string>).toString()
        : "";
      return fetchApi<ReportDetail[]>(`/api/reports${qs}`);
    },

    /** Phase 3: get a single report by ID */
    get: (id: string) => fetchApi<ReportDetail>(`/api/reports/${id}`),

    /** Phase 3: update report status (admin) */
    updateStatus: (id: string, body: UpdateStatusBody) =>
      fetchApi<ReportDetail>(`/api/reports/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    /** Phase 3: assign report to a department (admin) */
    assignDepartment: (id: string, body: { department_id: string }) =>
      fetchApi<ReportDetail>(`/api/reports/${id}/department`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
  },

  // ─── Departments ─────────────────────────────────────────────────────────
  departments: {
    list: () => fetchApi<Department[]>("/api/departments"),
  },

  // ─── Resident tracking (public, no auth) ─────────────────────────────────
  tracking: {
    get: (token: string) => fetchApi<TrackingInfo>(`/api/tracking/${token}`),
  },
};

// ─── Types (Phase 3: move to types/index.ts when schemas stabilize) ──────────

export type ReportSeverity = "low" | "medium" | "high" | "critical";
export type ReportStatus =
  | "submitted"
  | "reviewed"
  | "assigned"
  | "in_progress"
  | "resolved"
  | "duplicate"
  | "rejected";
export type ReportCategory =
  | "pothole"
  | "streetlight"
  | "flooding"
  | "sidewalk_damage"
  | "trash_overflow"
  | "damaged_sign"
  | "road_hazard"
  | "graffiti"
  | "snow_or_ice"
  | "other";

export interface CreateReportBody {
  description: string;
  latitude: number;
  longitude: number;
  address?: string;
  image_path?: string;
  contact_email?: string;
  contact_phone?: string;
}

export interface ReportResponse {
  id: string;
  status: ReportStatus;
  tracking_token: string;
  created_at: string;
}

export interface ReportDetail extends ReportResponse {
  description: string;
  latitude: number;
  longitude: number;
  address: string | null;
  category: ReportCategory | null;
  severity: ReportSeverity | null;
  department_id: string | null;
  updated_at: string;
}

export interface ListReportsParams {
  status: ReportStatus;
  category: ReportCategory;
  severity: ReportSeverity;
  department_id: string;
  bbox: string;
  limit: string;
  offset: string;
}

export interface UpdateStatusBody {
  status: ReportStatus;
  note?: string;
  public_note?: string;
}

export interface Department {
  id: string;
  name: string;
  description: string | null;
  contact_email: string | null;
  category_coverage: string[];
  created_at: string;
}

export interface TrackingInfo {
  status: string;
  category: string | null;
  created_at: string;
  public_note: string | null;
}
