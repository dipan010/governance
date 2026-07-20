import { useState } from "react";
import type { ApprovalRecord } from "../api/types";

export function ApprovalPanel({
  approvals,
  approvalRequired,
  onRequest,
  onDecide,
  busy,
}: {
  approvals: ApprovalRecord[];
  approvalRequired: boolean;
  onRequest: () => void;
  onDecide: (
    decision: "approve" | "reject" | "defer",
    approver: string,
    reason?: string,
  ) => void;
  busy: boolean;
}) {
  const [approver, setApprover] = useState("cloudgov-approver");
  const [reason, setReason] = useState("");
  const latest = approvals.at(-1) ?? null;
  const pending = latest?.status === "Requested";

  return (
    <section aria-label="Approval" className="panel">
      <h3>Approval</h3>
      <p>
        Status: <strong>{latest?.status ?? "NotRequested"}</strong>
        {latest?.approver ? ` by ${latest.approver}` : ""}
        {latest?.reason ? ` — reason: ${latest.reason}` : ""}
      </p>
      {!approvalRequired && <p className="hint">No approval required for this route.</p>}
      <button onClick={onRequest} disabled={busy || pending}>
        Request approval
      </button>
      {pending ? (
        <div className="decision-controls">
          <label>
            Approver
            <input value={approver} onChange={(e) => setApprover(e.target.value)} />
          </label>
          <label>
            Reason (required to reject/defer)
            <input value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>
          <button
            onClick={() => onDecide("approve", approver)}
            disabled={busy || !approver}
          >
            Approve
          </button>
          <button
            onClick={() => onDecide("reject", approver, reason)}
            disabled={busy || !approver || !reason}
          >
            Reject
          </button>
          <button
            onClick={() => onDecide("defer", approver, reason)}
            disabled={busy || !approver || !reason}
          >
            Defer
          </button>
        </div>
      ) : null}
      {latest ? (
        <details>
          <summary>Approval payload</summary>
          <pre>{JSON.stringify(latest.payload, null, 2)}</pre>
        </details>
      ) : null}
    </section>
  );
}
