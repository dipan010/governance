import type {
  ActionState,
  ApprovalDecision,
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
// Type-only import: erased at build time, so there is no runtime cycle
// between dataClient and its implementations.
import type { DataClient } from "./dataClient";
import {
  seedArtifacts,
  seedAudit,
  seedSecondaryArtifacts,
  seedViolations,
} from "./seed";

/**
 * In-memory implementation. Mutations persist for the session so the
 * approve → generate → verify journey behaves like the real thing.
 * Every call is async with simulated latency, so loading and error states
 * are exercised from day one.
 */

const LATENCY_MS = 420;

let violations: Violation[] = structuredClone(seedViolations);
const artifacts: Record<string, Artifact[]> = Object.fromEntries(
  violations.map((v) => {
    const list: Artifact[] = [];
    const primary = seedArtifacts[v.violationId];
    if (primary) list.push(structuredClone(primary));
    const secondary = seedSecondaryArtifacts[v.violationId];
    if (secondary) list.push(structuredClone(secondary));
    return [v.violationId, list];
  }),
);
const audit: Record<string, AuditEvent[]> = structuredClone(seedAudit);

function delay<T>(value: T, ms = LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

function find(id: string): Violation {
  const violation = violations.find((v) => v.violationId === id);
  if (!violation) {
    throw new Error(`Violation ${id} was not found`);
  }
  return violation;
}

function nowIso(): string {
  return new Date().toISOString();
}

function appendAudit(
  id: string,
  eventType: string,
  detail: string,
  extra: Partial<AuditEvent> = {},
): void {
  const trail = audit[id] ?? (audit[id] = []);
  trail.push({
    eventId: `ev-${id}-${trail.length + 1}`,
    violationId: id,
    eventType,
    correlationId: `corr-${id.toLowerCase()}-live`,
    actionId: null,
    promptRunId: "P19",
    evidencePacket: null,
    detail,
    createdAt: nowIso(),
    ...extra,
  });
}

function matches(violation: Violation, filters: WorklistFilters): boolean {
  const { ownership, riskSignals, resourceFacts, decision, actionState } =
    violation;
  const exposure = riskSignals.internetExposure
    ? "internet exposed"
    : "private only";
  const checks: Array<[string | undefined, string]> = [
    [filters.policy, violation.policyEvidence.policyId],
    [filters.severity, riskSignals.severity],
    [filters.riskBand, decision.riskBand],
    [filters.exposure, exposure],
    [filters.dataClassification, riskSignals.dataClassification],
    [filters.owner, ownership.ownerTeam ?? "Owner gap"],
    [filters.app, ownership.businessApp ?? "—"],
    [filters.sourceDrift, String(violation.history.sourceDriftLikely)],
    [filters.route, decision.recommendedPath],
    [filters.confidence, ownership.ownerConfidence],
    [filters.status, actionState.actionStatus],
  ];
  for (const [wanted, actual] of checks) {
    if (wanted && wanted !== actual) return false;
  }
  if (filters.blocker && !decision.blockers.includes(filters.blocker)) {
    return false;
  }
  if (
    filters.policy &&
    filters.policy !== violation.policyEvidence.policyId &&
    filters.policy !== resourceFacts.resourceType
  ) {
    return false;
  }
  return true;
}

export const mockClient: DataClient = {
  async ingestPolicy(): Promise<IngestResult> {
    violations = structuredClone(seedViolations);
    return delay({
      ingestId: crypto.randomUUID(),
      ingested: violations.length,
      errors: 0,
    });
  },

  async ingestDefender(): Promise<IngestResult> {
    return delay({ ingestId: crypto.randomUUID(), ingested: 0, errors: 0 });
  },

  async listViolations(filters: WorklistFilters = {}): Promise<Violation[]> {
    const result = violations.filter((v) => matches(v, filters));
    return delay(structuredClone(result));
  },

  async getViolation(id: string): Promise<Violation> {
    const violation = structuredClone(find(id));
    return delay(violation);
  },

  async score(id: string): Promise<Decision> {
    // The server owns scoring. The mock returns the stored decision
    // unchanged — it never recalculates.
    return delay(structuredClone(find(id).decision));
  },

  async route(id: string): Promise<RouteRecommendation> {
    const { decision, violationId } = find(id);
    return delay({
      violationId,
      route: decision.recommendedPath,
      reason: decision.routeReason,
      blockers: [...decision.blockers],
      approvalRequired: decision.approvalRequired,
      approverRole: decision.approverRole,
      sideEffects: [...decision.sideEffects],
      rollbackOrNextAction: decision.rollbackOrNextAction,
      routeRuleVersion: decision.routeRuleVersion,
    });
  },

  async requestApproval(id: string): Promise<ApprovalPayload> {
    const violation = find(id);
    violation.actionState.approvalState = "Requested";
    if (violation.actionState.actionStatus === "Open") {
      violation.actionState.actionStatus = "AwaitingApproval";
    }
    appendAudit(
      id,
      "approval.requested",
      `Approver role: ${violation.decision.approverRole ?? "unassigned"}`,
    );
    const expectedAfterState = Object.fromEntries(
      violation.sourceMap.map((entry) => [
        entry.runtimeProperty,
        entry.expectedValue,
      ]),
    );
    return delay({
      approvalId: `apr-${id}`,
      violationId: id,
      approvalState: violation.actionState.approvalState,
      approverRole: violation.decision.approverRole,
      route: violation.decision.recommendedPath,
      riskScore: violation.decision.riskScore,
      riskBand: violation.decision.riskBand,
      blastRadius: `${violation.riskSignals.dependencyCount ?? "unknown"} dependent resources · ${violation.resourceFacts.environment}`,
      affectedResources: [violation.resourceFacts.resourceId],
      restartRisk: violation.remediationEligibility.restartRisk,
      downtimeRisk: violation.remediationEligibility.downtimeRisk,
      expectedAfterState:
        Object.keys(expectedAfterState).length > 0
          ? expectedAfterState
          : { compliant: violation.verification.expectedCompliantValue },
      rollbackOrNextAction: violation.decision.rollbackOrNextAction,
      verificationQuery: violation.verification.verificationQuery,
      requestedAt: nowIso(),
    });
  },

  async approve(id: string, decision: ApprovalDecision): Promise<ActionState> {
    const violation = find(id);
    if (violation.actionState.approvalState !== "Requested") {
      throw new Error(
        `Approval for ${id} has not been requested yet — request it first`,
      );
    }
    if (decision.decision === "reject" && !decision.reason) {
      throw new Error("A reason is required to reject an approval");
    }
    const state = violation.actionState;
    if (decision.decision === "approve") {
      state.approvalState = "Approved";
      state.actionStatus = "Approved";
      state.approver = decision.approver;
      state.approvedAt = nowIso();
      state.rejectionReason = null;
      appendAudit(id, "approval.approved", `Approved by ${decision.approver}`);
    } else {
      state.approvalState = "Rejected";
      state.actionStatus = "Rejected";
      state.approver = decision.approver;
      state.rejectionReason = decision.reason ?? null;
      appendAudit(
        id,
        "approval.rejected",
        `Rejected by ${decision.approver}: ${decision.reason}`,
      );
    }
    return delay(structuredClone(state));
  },

  async generateArtifact(id: string): Promise<Artifact> {
    const violation = find(id);
    const { approvalRequired } = violation.decision;
    if (approvalRequired && violation.actionState.approvalState !== "Approved") {
      throw new Error(
        `This route requires approval before an artifact can be generated (current state: ${violation.actionState.approvalState})`,
      );
    }
    const existing = artifacts[id]?.[0];
    if (!existing) {
      throw new Error(`No artifact template exists for ${id}`);
    }
    const artifact: Artifact = {
      ...structuredClone(existing),
      artifactId: `${existing.artifactId}-${Date.now()}`,
      createdAt: nowIso(),
    };
    if (violation.actionState.actionStatus !== "Blocked") {
      violation.actionState.actionStatus = "ArtifactCreated";
    }
    if (artifact.kind === "ticket" && !violation.actionState.ticketId) {
      violation.actionState.ticketId = "CHG-48213";
    }
    if (artifact.kind === "remediation_dry_run") {
      violation.actionState.remediationTaskId = `DRYRUN-${id}`;
    }
    appendAudit(id, "artifact.generated", `${artifact.kind} (draft)`, {
      actionId: artifact.artifactId,
    });
    return delay(artifact);
  },

  async verify(id: string): Promise<Verification> {
    const violation = find(id);
    const verification = violation.verification;
    if (!verification.afterState) {
      // Simulate the post-change re-query: the expected compliant values
      // become the observed after-state.
      const after: Record<string, string> = {};
      for (const entry of violation.sourceMap) {
        after[entry.runtimeProperty] = entry.expectedValue;
      }
      if (Object.keys(after).length === 0) {
        for (const key of Object.keys(verification.beforeState ?? {})) {
          after[key] = "compliant";
        }
      }
      verification.afterState = after;
      verification.verificationResult = "Compliant";
      verification.nextAction =
        "Close the violation; the evidence packet holds before/after proof";
      violation.actionState.actionStatus = "Verified";
      appendAudit(
        id,
        "verification.completed",
        `Re-query returned the expected compliant values; result Compliant`,
        {
          evidencePacket: `evidence_packets/${id}/verification.completed-${Date.now()}.json`,
        },
      );
    }
    return delay(structuredClone(verification));
  },

  async dashboardSummary(): Promise<DashboardSummary> {
    const all = violations;
    const ranked = [...all].sort(
      (a, b) => b.decision.riskScore - a.decision.riskScore,
    );
    const isBlocked = (v: Violation) =>
      v.decision.recommendedPath === "blocked_manual_review" ||
      v.actionState.actionStatus === "Blocked";
    const highRisk = ranked.filter((v) => v.decision.riskScore >= 60);

    return delay({
      totalFindings: all.length,
      criticalFindings: all.filter((v) => v.decision.riskBand === "Critical")
        .length,
      repeatViolations: all.filter((v) => v.history.recurrenceCount > 0).length,
      autoRemediable: all.filter(
        (v) => v.decision.recommendedPath === "remediation_dry_run",
      ).length,
      tickets: Object.values(artifacts)
        .flat()
        .filter((a) => a.kind === "ticket").length,
      prComments: Object.values(artifacts)
        .flat()
        .filter((a) => a.kind === "pr_comment_preview").length,
      exceptions: Object.values(artifacts)
        .flat()
        .filter((a) => a.kind === "exception_request").length,
      blockedUnsafeActions: all.filter(isBlocked).length,
      verifiedFixes: all.filter(
        (v) => v.verification.verificationResult === "Compliant",
      ).length,
      highRiskActionable: highRisk
        .filter((v) => !isBlocked(v))
        .map((v) => ({
          violationId: v.violationId,
          policyName: v.policyEvidence.policyName,
          riskScore: v.decision.riskScore,
          riskBand: v.decision.riskBand,
          route: v.decision.recommendedPath,
        })),
      highRiskBlocked: highRisk
        .filter(isBlocked)
        .map((v) => ({
          violationId: v.violationId,
          policyName: v.policyEvidence.policyName,
          riskScore: v.decision.riskScore,
          riskBand: v.decision.riskBand,
          blockers: [...v.decision.blockers],
        })),
    });
  },

  async auditTrail(id: string): Promise<AuditEvent[]> {
    find(id); // 404 semantics for unknown IDs
    return delay(structuredClone(audit[id] ?? []));
  },
};
