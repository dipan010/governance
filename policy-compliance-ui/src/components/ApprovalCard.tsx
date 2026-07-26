import { useState } from "react";
import { formatDateTime, humanize } from "../lib/format";
import type { ApprovalDecision, ApprovalPayload, Violation } from "../types";
import { RiskBandBadge } from "./RiskBandBadge";

export function ApprovalCard({
  violation,
  payload,
  busy,
  onRequest,
  onDecide,
}: {
  violation: Violation;
  payload: ApprovalPayload | null;
  busy: boolean;
  onRequest: () => void;
  onDecide: (decision: ApprovalDecision) => void;
}) {
  const [approver, setApprover] = useState("cloudgov-approver");
  const [reason, setReason] = useState("");
  const { decision, actionState, remediationEligibility } = violation;
  const state = actionState.approvalState;
  const pending = state === "Requested";

  const expectedAfterState =
    payload?.expectedAfterState ??
    Object.fromEntries(
      violation.sourceMap.map((e) => [e.runtimeProperty, e.expectedValue]),
    );

  return (
    <section className="card card-pad flex flex-col gap-4" aria-label="Approval">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Approval</h2>
        <span
          className={`chip ${
            state === "Approved"
              ? "border-success/40 bg-success/10 text-success"
              : state === "Rejected"
                ? "border-danger/40 bg-danger/10 text-danger"
                : "border-line bg-surface-sunken text-ink-muted"
          }`}
        >
          {state}
        </span>
      </header>

      <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
        <div>
          <dt className="label">Approval required</dt>
          <dd className="value font-semibold">
            {decision.approvalRequired ? "Yes" : "No"}
          </dd>
        </div>
        <div>
          <dt className="label">Approver role</dt>
          <dd className="value">{decision.approverRole ?? "—"}</dd>
        </div>
        <div>
          <dt className="label">Risk</dt>
          <dd className="mt-0.5">
            <RiskBandBadge band={decision.riskBand} score={decision.riskScore} />
          </dd>
        </div>
        <div>
          <dt className="label">Blast radius</dt>
          <dd className="value">
            {payload?.blastRadius ??
              `${violation.riskSignals.dependencyCount ?? "unknown"} dependent resources · ${violation.resourceFacts.environment}`}
          </dd>
        </div>
        <div>
          <dt className="label">Downtime risk</dt>
          <dd className="value">{remediationEligibility.downtimeRisk}</dd>
        </div>
        <div>
          <dt className="label">Restart risk</dt>
          <dd className="value">{remediationEligibility.restartRisk}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="label">Affected resources</dt>
          <dd className="mono mt-0.5 break-all text-ink">
            {(payload?.affectedResources ?? [violation.resourceFacts.resourceId]).join(
              ", ",
            )}
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="label">Expected after-state</dt>
          <dd className="mt-1 flex flex-wrap gap-1.5">
            {Object.entries(expectedAfterState).length === 0 ? (
              <span className="text-sm text-ink-muted">
                {violation.verification.expectedCompliantValue}
              </span>
            ) : (
              Object.entries(expectedAfterState).map(([key, value]) => (
                <span
                  key={key}
                  className="chip border-success/40 bg-success/10 text-success"
                >
                  <span className="font-mono">{key}</span>= {value}
                </span>
              ))
            )}
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="label">Rollback / next action</dt>
          <dd className="value">{decision.rollbackOrNextAction}</dd>
        </div>
      </dl>

      {actionState.approver && (
        <p className="text-sm text-ink-muted">
          {state === "Approved" ? "Approved" : "Decided"} by{" "}
          <strong className="text-ink">{actionState.approver}</strong>
          {actionState.approvedAt
            ? ` on ${formatDateTime(actionState.approvedAt)}`
            : ""}
          {actionState.rejectionReason
            ? ` — reason: ${actionState.rejectionReason}`
            : ""}
        </p>
      )}

      {decision.blockers.length > 0 && (
        <p className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          Safety blockers restrict this action:{" "}
          {decision.blockers.map(humanize).join(", ")}.
        </p>
      )}

      <div className="flex flex-col gap-3 border-t border-line pt-3">
        {state === "NotRequested" && (
          <div>
            <button
              type="button"
              className="btn-primary"
              onClick={onRequest}
              disabled={busy || !decision.approvalRequired}
              title={
                decision.approvalRequired
                  ? undefined
                  : "This route does not require approval"
              }
            >
              Request approval
            </button>
            {!decision.approvalRequired && (
              <p className="mt-1.5 text-[13px] text-ink-muted">
                No approval is required for this route — it produces drafts only.
              </p>
            )}
          </div>
        )}

        {pending && (
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-3">
              <label className="flex flex-col gap-1">
                <span className="label">Approver</span>
                <input
                  className="field w-56"
                  value={approver}
                  onChange={(event) => setApprover(event.target.value)}
                />
              </label>
              <label className="flex flex-1 flex-col gap-1">
                <span className="label">Reason (required to reject)</span>
                <input
                  className="field"
                  value={reason}
                  placeholder="e.g. outside the approved change window"
                  onChange={(event) => setReason(event.target.value)}
                />
              </label>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="btn-primary"
                disabled={busy || !approver}
                onClick={() => onDecide({ decision: "approve", approver })}
              >
                Approve
              </button>
              <button
                type="button"
                className="btn-danger"
                disabled={busy || !approver || !reason}
                title={reason ? undefined : "A reason is required to reject"}
                onClick={() =>
                  onDecide({ decision: "reject", approver, reason })
                }
              >
                Reject
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
