import type {
  ApprovalDecision,
  ApprovalPayload,
  Artifact,
  AuditEvent,
  ActionState,
  DashboardSummary,
  Decision,
  IngestResult,
  RouteRecommendation,
  Verification,
  Violation,
  WorklistFilters,
} from "../types";
import { apiClient } from "./apiClient";
import { mockClient } from "./mockClient";

/**
 * The single seam between the UI and its data source. Every screen imports
 * from this module only — nothing else touches mockClient or apiClient.
 *
 * Signatures map 1:1 onto the backend API, so pointing the console at the
 * real FastAPI service is a one-flag change (VITE_USE_MOCK=false).
 *
 * Scoring, routing, approval, and closure are SERVER responsibilities. The
 * client displays what the server decided; it never computes a final score,
 * picks a route, or closes a finding on its own.
 */
export interface DataClient {
  /** POST /api/ingest/policy */
  ingestPolicy(payload: unknown): Promise<IngestResult>;
  /** POST /api/ingest/defender */
  ingestDefender(payload: unknown): Promise<IngestResult>;
  /** GET /api/violations */
  listViolations(filters?: WorklistFilters): Promise<Violation[]>;
  /** GET /api/violations/{id} */
  getViolation(id: string): Promise<Violation>;
  /** POST /api/violations/{id}/score */
  score(id: string): Promise<Decision>;
  /** POST /api/violations/{id}/route */
  route(id: string): Promise<RouteRecommendation>;
  /** POST /api/violations/{id}/approval-request */
  requestApproval(id: string): Promise<ApprovalPayload>;
  /** POST /api/violations/{id}/approve */
  approve(id: string, decision: ApprovalDecision): Promise<ActionState>;
  /** POST /api/violations/{id}/artifact */
  generateArtifact(id: string): Promise<Artifact>;
  /** POST /api/violations/{id}/verify */
  verify(id: string): Promise<Verification>;
  /** GET /api/dashboard/summary */
  dashboardSummary(): Promise<DashboardSummary>;
  /** GET /api/audit/{violationId} */
  auditTrail(id: string): Promise<AuditEvent[]>;
}

const useMock = import.meta.env.VITE_USE_MOCK !== "false";

export const dataClient: DataClient = useMock ? mockClient : apiClient;

export const dataSourceLabel = useMock ? "Mock data" : "Live API";
