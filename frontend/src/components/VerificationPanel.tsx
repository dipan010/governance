import type { Evidence } from "../api/types";

export function VerificationPanel({
  evidence,
  onVerify,
  onClose,
  busy,
}: {
  evidence: Evidence;
  onVerify: () => void;
  onClose: () => void;
  busy: boolean;
}) {
  const verification = evidence.verification;
  const compliant = verification.verificationResult === "Compliant";
  const canVerify = Boolean(verification.verificationQuery);

  return (
    <section aria-label="Verification" className="panel">
      <h3>Verification</h3>
      <p>
        Result: <strong>{verification.verificationResult}</strong>
      </p>
      {verification.verificationQuery ? (
        <p className="query">
          Query: <code>{verification.verificationQuery}</code>
        </p>
      ) : (
        <p className="missing">Verification query missing — cannot close.</p>
      )}
      <p>Expected: {verification.expectedCompliantValue ?? "–"}</p>
      <div className="states">
        <div>
          <h4>Before</h4>
          <pre>{JSON.stringify(verification.beforeState, null, 2)}</pre>
        </div>
        <div>
          <h4>After</h4>
          <pre>{JSON.stringify(verification.afterState, null, 2)}</pre>
        </div>
      </div>
      {verification.nextAction ? <p>Next action: {verification.nextAction}</p> : null}
      <button onClick={onVerify} disabled={busy || !canVerify}>
        Run verification
      </button>
      <button
        onClick={onClose}
        disabled={busy || !compliant}
        title={compliant ? undefined : "Closure requires after-state proof"}
      >
        Close violation
      </button>
      {!compliant ? (
        <p className="hint">Close is disabled until verification proves compliance.</p>
      ) : null}
    </section>
  );
}
