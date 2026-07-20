import type { Artifact, Decision } from "../api/types";

const ROUTE_LABELS: Record<string, string> = {
  source_pr_plus_change_ticket: "Source PR/comment plus change ticket",
  remediation_dry_run: "Remediation dry-run (after approval)",
  owner_ticket_or_change_request: "Owner ticket / change request",
  time_bound_exception: "Time-bound exception",
  blocked_manual_review: "Blocked: manual review",
  escalation: "Escalation",
  observe: "Observe",
  invalid_finding: "Invalid finding",
};

export function RouteView({
  decision,
  artifacts,
  approvalState,
  verificationQuery,
  onGenerate,
  busy,
}: {
  decision: Decision;
  artifacts: Artifact[];
  approvalState: string;
  verificationQuery: string | null;
  onGenerate: () => void;
  busy: boolean;
}) {
  const route = decision.recommendedPath;
  const needsApproval = decision.approvalRequired === true;
  const approved = approvalState === "Approved";
  const generateDisabled = busy || (needsApproval && !approved);

  return (
    <section aria-label="Recommended route" className="panel">
      <h3>Recommended route</h3>
      <p className="route-name">{route ? (ROUTE_LABELS[route] ?? route) : "unrouted"}</p>
      <p>
        Approval required: <strong>{needsApproval ? "yes" : "no"}</strong>
        {decision.approverRole ? ` (${decision.approverRole})` : ""}
      </p>
      <p>
        Next action: <strong>{decision.rollbackOrNextAction ?? "–"}</strong>
      </p>
      {verificationQuery ? (
        <p className="query">
          Verification query: <code>{verificationQuery}</code>
        </p>
      ) : (
        <p className="missing">Verification query missing</p>
      )}
      <button
        onClick={onGenerate}
        disabled={generateDisabled}
        aria-label="Generate route artifact"
        title={
          generateDisabled && needsApproval && !approved
            ? "Approval required before this action"
            : undefined
        }
      >
        Generate artifact
      </button>
      {needsApproval && !approved ? (
        <p className="hint">Disabled until an approval is granted.</p>
      ) : null}
      {artifacts.map((artifact) => (
        <details key={artifact.artifactId} className="artifact">
          <summary>
            {artifact.kind} {artifact.isDraft ? "(draft)" : ""} —{" "}
            {artifact.approvalState}
          </summary>
          <pre>{artifact.body}</pre>
        </details>
      ))}
    </section>
  );
}
