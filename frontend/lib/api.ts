const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// ─── Fetch helper ─────────────────────────────────────────────────────────────

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

// ─── API client ───────────────────────────────────────────────────────────────

export const api = {
  health: () => fetchApi<{ status: string; version: string }>("/health"),

  upload: {
    /** Upload a report image; returns storage path and public URL. */
    image: async (file: File): Promise<UploadImageResponse> => {
      const form = new FormData();
      form.append("file", file);
      const url = `${BASE_URL}/api/upload/image`;
      const res = await fetch(url, { method: "POST", body: form });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Upload failed ${res.status}: ${text}`);
      }
      return res.json() as Promise<UploadImageResponse>;
    },
  },

  reports: {
    /** Submit a new civic issue report. */
    create: (body: CreateReportBody) =>
      fetchApi<ReportResponse>("/api/reports", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** List reports with optional filters. */
    list: (params?: Partial<ListReportsParams>) => {
      const qs = params
        ? "?" + new URLSearchParams(params as Record<string, string>).toString()
        : "";
      return fetchApi<ReportDetail[]>(`/api/reports${qs}`);
    },

    /** Get a single report by ID. */
    get: (id: string) => fetchApi<ReportDetail>(`/api/reports/${id}`),

    /** Update report status (admin). */
    updateStatus: (id: string, body: UpdateStatusBody) =>
      fetchApi<ReportDetail>(`/api/reports/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    /** Assign report to a department (admin). */
    assignDepartment: (id: string, body: { department_id: string }) =>
      fetchApi<ReportDetail>(`/api/reports/${id}/department`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
  },

  departments: {
    list: () => fetchApi<Department[]>("/api/departments"),
  },

  tracking: {
    /** Public tracking endpoint — no auth required. */
    get: (token: string) =>
      fetchApi<TrackingReport>(`/api/tracking/${token}`),
  },
};

// ─── Types ────────────────────────────────────────────────────────────────────

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

export interface UploadImageResponse {
  storage_path: string;
  public_url: string;
}

export interface CreateReportBody {
  description: string;
  latitude: number;
  longitude: number;
  address?: string;
  /** Storage path returned by POST /api/upload/image */
  image_path?: string;
  contact_email?: string;
  contact_phone?: string;
}

export interface ReportResponse {
  id: string;
  status: ReportStatus;
  category: ReportCategory | null;
  tracking_token: string;
  created_at: string;
}

export interface ReportDetail extends ReportResponse {
  description: string;
  latitude: number;
  longitude: number;
  address: string | null;
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
  slug: string;
  name: string;
  description: string | null;
  contact_email: string | null;
  category_coverage: string[];
  created_at: string;
}

export interface TrackingReport {
  tracking_token: string;
  status: ReportStatus;
  category: ReportCategory | null;
  severity: ReportSeverity | null;
  address: string | null;
  created_at: string;
  updated_at: string | null;
  public_note: string | null;
}
