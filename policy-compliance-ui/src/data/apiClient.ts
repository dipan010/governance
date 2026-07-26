import type {
  ActionState,
  ApprovalPayload,
  Artifact,
  AuditEvent,
  DashboardSummary,
  Decision,
  IngestResult,
  RouteRecommendation,
  Verification,
  Violation,
  WorklistFilters,
} from "../types";
import type { DataClient } from "./dataClient";

/**
 * Real backend implementation. Enabled by setting VITE_USE_MOCK=false;
 * no other file changes. Endpoint paths match the FastAPI service exactly.
 */

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: unknown,
  ) {
    super(
      typeof detail === "object" && detail !== null && "reason" in detail
        ? String((detail as { reason: unknown }).reason)
        : `Request failed with status ${status}`,
    );
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, (body as { detail?: unknown }).detail);
  }
  return (await response.json()) as T;
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

function queryString(filters: WorklistFilters = {}): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const apiClient: DataClient = {
  ingestPolicy: (payload) => post<IngestResult>("/api/ingest/policy", payload),
  ingestDefender: (payload) =>
    post<IngestResult>("/api/ingest/defender", payload),
  listViolations: (filters) =>
    request<Violation[]>(`/api/violations${queryString(filters)}`),
  getViolation: (id) => request<Violation>(`/api/violations/${id}`),
  score: (id) => post<Decision>(`/api/violations/${id}/score`),
  route: (id) => post<RouteRecommendation>(`/api/violations/${id}/route`),
  requestApproval: (id) =>
    post<ApprovalPayload>(`/api/violations/${id}/approval-request`),
  approve: (id, decision) =>
    post<ActionState>(`/api/violations/${id}/approve`, decision),
  generateArtifact: (id) => post<Artifact>(`/api/violations/${id}/artifact`),
  verify: (id) => post<Verification>(`/api/violations/${id}/verify`),
  dashboardSummary: () => request<DashboardSummary>("/api/dashboard/summary"),
  auditTrail: (id) => request<AuditEvent[]>(`/api/audit/${id}`),
};
