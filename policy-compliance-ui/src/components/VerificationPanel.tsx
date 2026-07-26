import type { Verification } from "../types";

function StateBlock({
  title,
  state,
  tone,
}: {
  title: string;
  state: Record<string, string> | null;
  tone: "before" | "after";
}) {
  return (
    <div className="flex-1">
      <p className="label mb-1">{title}</p>
      {state ? (
        <ul className="flex flex-col gap-1">
          {Object.entries(state).map(([key, value]) => (
            <li
              key={key}
              className={`mono rounded border px-2 py-1 ${
                tone === "before"
                  ? "border-danger/30 bg-danger/5 text-ink"
                  : "border-success/30 bg-success/5 text-ink"
              }`}
            >
              <span className="text-ink-subtle">{key}</span> = {value}
            </li>
          ))}
        </ul>
      ) : (
        <p className="rounded border border-dashed border-line px-2 py-3 text-center text-xs text-ink-subtle">
          Not captured yet
        </p>
      )}
    </div>
  );
}

export function VerificationPanel({
  verification,
  busy,
  onVerify,
}: {
  verification: Verification;
  busy: boolean;
  onVerify: () => void;
}) {
  const result = verification.verificationResult;
  const resultClass = {
    Compliant: "border-success/40 bg-success/10 text-success",
    Failed: "border-danger/40 bg-danger/10 text-danger",
    NotRun: "border-line bg-surface-sunken text-ink-muted",
  }[result];

  return (
    <section className="card card-pad flex flex-col gap-4" aria-label="Verification">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Verification</h2>
        <span className={`chip ${resultClass}`}>{result}</span>
      </header>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <StateBlock title="Before" state={verification.beforeState} tone="before" />
        <span
          aria-hidden="true"
          className="hidden self-center text-lg text-ink-subtle sm:block"
        >
          →
        </span>
        <StateBlock title="After" state={verification.afterState} tone="after" />
      </div>

      <div>
        <p className="label">Verification query</p>
        <pre className="pre-block mt-1 whitespace-pre-wrap">
          {verification.verificationQuery}
        </pre>
      </div>

      <div>
        <p className="label">Expected compliant value</p>
        <p className="mono mt-0.5 text-ink">{verification.expectedCompliantValue}</p>
      </div>

      <div>
        <p className="label">Next action</p>
        <p className="value">{verification.nextAction}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-line pt-3">
        <button
          type="button"
          className="btn-primary"
          onClick={onVerify}
          disabled={busy || result === "Compliant"}
        >
          Run verification
        </button>
        <p className="text-[13px] text-ink-muted">
          {result === "Compliant"
            ? "After-state proof is stored; this finding may now be closed."
            : "Nothing closes without before/after proof — closure is a server decision."}
        </p>
      </div>
    </section>
  );
}
