import type { Artifact, AuditEvent, ViolationDetail } from "../api/types";
import { ApprovalPanel } from "./ApprovalPanel";
import { AuditTimeline } from "./AuditTimeline";
import { RouteView } from "./RouteView";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { SourceFixPanel } from "./SourceFixPanel";
import { VerificationPanel } from "./VerificationPanel";

export function FindingCard({
  detail,
  artifacts,
  audit,
  busy,
  onRequestApproval,
  onDecideApproval,
  onGenerateArtifacts,
  onVerify,
  onClose,
}: {
  detail: ViolationDetail;
  artifacts: Artifact[];
  audit: AuditEvent[];
  busy: boolean;
  onRequestApproval: () => void;
  onDecideApproval: (
    decision: "approve" | "reject" | "defer",
    approver: string,
    reason?: string,
  ) => void;
  onGenerateArtifacts: () => void;
  onVerify: () => void;
  onClose: () => void;
}) {
  const { evidence } = detail;
  const approvalState = detail.approvals.at(-1)?.status ?? "NotRequested";
  const exposure =
    evidence.riskSignals.internetExposure === true
      ? "internet exposed"
      : evidence.riskSignals.internetExposure === false
        ? "private only"
        : "unknown";

  return (
    <article className="finding-card" aria-label={`Finding ${detail.violationId}`}>
      <header>
        <h2>
          {detail.violationId} — {evidence.policyEvidence.policyName}
        </h2>
        <p className="status-line">
          Status: <strong>{evidence.actionState.actionStatus}</strong> · Severity:{" "}
          {evidence.riskSignals.severity} · Confidence: owner{" "}
          {evidence.ownership.ownerConfidence} / source {evidence.history.sourceConfidence}
        </p>
      </header>

      <section aria-label="Resource context" className="panel">
        <h3>Resource context</h3>
        <p>
          <code>{evidence.resourceFacts.resourceId}</code>
        </p>
        <p>
          {evidence.resourceFacts.resourceType} · {evidence.resourceFacts.environment} ·{" "}
          {exposure} · data: {evidence.riskSignals.dataClassification}
        </p>
        <p>
          Owner:{" "}
          <strong>
            {evidence.ownership.ownerTeam ?? "OWNER GAP — missing owner"}
          </strong>
          {evidence.ownership.businessApp ? ` · app: ${evidence.ownership.businessApp}` : ""}
        </p>
        {detail.missingEvidence.length ? (
          <p className="missing" aria-label="Missing evidence">
            Missing evidence: {detail.missingEvidence.join(", ")}
          </p>
        ) : null}
      </section>

      <section aria-label="Raw evidence" className="panel">
        <h3>Raw evidence</h3>
        <p>
          {evidence.policyEvidence.complianceState}:{" "}
          {evidence.policyEvidence.failureReason ?? "no failure reason"} (evaluated{" "}
          {evidence.policyEvidence.evaluatedAt})
        </p>
        <p>
          Focused signals:{" "}
          {evidence.riskSignals.focusedSignals.length
            ? evidence.riskSignals.focusedSignals.join(", ")
            : "none"}
        </p>
      </section>

      <ScoreBreakdown decision={evidence.decision} />
      <RouteView
        decision={evidence.decision}
        artifacts={artifacts}
        approvalState={approvalState}
        verificationQuery={evidence.verification.verificationQuery}
        onGenerate={onGenerateArtifacts}
        busy={busy}
      />
      <ApprovalPanel
        approvals={detail.approvals}
        approvalRequired={evidence.decision.approvalRequired === true}
        onRequest={onRequestApproval}
        onDecide={onDecideApproval}
        busy={busy}
      />
      <SourceFixPanel evidence={evidence} />
      <VerificationPanel
        evidence={evidence}
        onVerify={onVerify}
        onClose={onClose}
        busy={busy}
      />
      <AuditTimeline events={audit} />
    </article>
  );
}
