import type {
  ApprovalRecord,
  Artifact,
  AuditEvent,
  DashboardSummary,
  SortMode,
  VerifyResponse,
  ViolationDetail,
  ViolationSummary,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body);
  }
  return (await response.json()) as T;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API error ${status}`);
  }
}

export const api = {
  summary: () => request<DashboardSummary>("/api/dashboard/summary"),
  violations: (sort: SortMode) =>
    request<ViolationSummary[]>(`/api/violations?sort=${sort}`),
  violation: (id: string) => request<ViolationDetail>(`/api/violations/${id}`),
  artifacts: (id: string) => request<Artifact[]>(`/api/violations/${id}/artifacts`),
  audit: (id: string) => request<AuditEvent[]>(`/api/audit/${id}`),
  requestApproval: (id: string) =>
    request<ApprovalRecord>(`/api/violations/${id}/approval-request`, {
      method: "POST",
    }),
  decideApproval: (
    id: string,
    decision: "approve" | "reject" | "defer",
    approver: string,
    reason?: string,
  ) =>
    request<ApprovalRecord>(`/api/violations/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ decision, approver, reason }),
    }),
  generateArtifacts: (id: string) =>
    request<Artifact[]>(`/api/violations/${id}/artifact`, { method: "POST" }),
  verify: (id: string) =>
    request<VerifyResponse>(`/api/violations/${id}/verify`, { method: "POST" }),
  close: (id: string) =>
    request<{ violationId: string; actionStatus: string }>(
      `/api/violations/${id}/close`,
      { method: "POST" },
    ),
};
