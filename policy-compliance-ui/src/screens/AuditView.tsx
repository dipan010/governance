import { Link, useParams } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { Skeleton } from "../components/Skeleton";
import { formatDateTime } from "../lib/format";
import { useAuditTrail, useViolation } from "../store/useViolations";

const EVENT_TONE: Record<string, string> = {
  "approval.approved": "border-success/40 bg-success/10 text-success",
  "approval.rejected": "border-danger/40 bg-danger/10 text-danger",
  "violation.blocked": "border-danger/40 bg-danger/10 text-danger",
  "verification.completed": "border-success/40 bg-success/10 text-success",
  "violation.closed": "border-success/40 bg-success/10 text-success",
  "exception.created": "border-warning/40 bg-warning/10 text-warning",
};

export function AuditView() {
  const { id = "" } = useParams();
  const { data: violation } = useViolation(id);
  const { data: events, loading, error, reload } = useAuditTrail(id);

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-ink">
            {id} — audit trail
          </h1>
          <p className="mt-1 text-sm text-ink-muted">
            Append-only evidence. Every decision records a correlation ID and
            the prompt run that produced the behavior.
          </p>
        </div>
        <div className="flex gap-2">
          <Link className="btn-secondary" to={`/violations/${id}`}>
            Finding card
          </Link>
          <Link className="btn-secondary" to={`/violations/${id}/route`}>
            Route view
          </Link>
        </div>
      </header>

      {violation && (
        <section
          className="card card-pad grid gap-x-6 gap-y-3 sm:grid-cols-2"
          aria-label="Verification evidence"
        >
          <div>
            <p className="label">Before state</p>
            <ul className="mt-1 flex flex-col gap-1">
              {Object.entries(violation.verification.beforeState ?? {}).map(
                ([key, value]) => (
                  <li key={key} className="mono text-ink">
                    <span className="text-ink-subtle">{key}</span> = {value}
                  </li>
                ),
              )}
            </ul>
          </div>
          <div>
            <p className="label">After state</p>
            {violation.verification.afterState ? (
              <ul className="mt-1 flex flex-col gap-1">
                {Object.entries(violation.verification.afterState).map(
                  ([key, value]) => (
                    <li key={key} className="mono text-success">
                      <span className="text-ink-subtle">{key}</span> = {value}
                    </li>
                  ),
                )}
              </ul>
            ) : (
              <p className="mt-1 text-sm text-ink-muted">
                Not captured — this finding cannot close yet.
              </p>
            )}
          </div>
          <div>
            <p className="label">Approver</p>
            <p className="value">{violation.actionState.approver ?? "—"}</p>
          </div>
          <div>
            <p className="label">Action ID</p>
            <p className="mono text-ink">
              {violation.actionState.ticketId ??
                violation.actionState.remediationTaskId ??
                "—"}
            </p>
          </div>
          <div className="sm:col-span-2">
            <p className="label">Next action</p>
            <p className="value">{violation.verification.nextAction}</p>
          </div>
        </section>
      )}

      {loading && (
        <div className="flex flex-col gap-2" role="status" aria-label="Loading audit trail">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-14 w-full" />
          ))}
        </div>
      )}

      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && events && events.length === 0 && (
        <EmptyState
          title="No audit events yet"
          description="Events appear as the finding moves through scoring, routing, approval, artifacts, and verification."
        />
      )}

      {!loading && !error && events && events.length > 0 && (
        <ol className="flex flex-col gap-2" aria-label="Audit events">
          {events.map((event) => (
            <li key={event.eventId} className="card card-pad flex flex-col gap-1.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span
                  className={`chip ${
                    EVENT_TONE[event.eventType] ??
                    "border-line bg-surface-sunken text-ink-muted"
                  }`}
                >
                  {event.eventType}
                </span>
                <time className="text-[11px] text-ink-subtle">
                  {formatDateTime(event.createdAt)}
                </time>
              </div>
              <p className="text-sm text-ink">{event.detail}</p>
              <p className="flex flex-wrap gap-x-4 text-[11px] text-ink-subtle">
                <span>correlation {event.correlationId}</span>
                <span>prompt run {event.promptRunId}</span>
                {event.actionId && <span>action {event.actionId}</span>}
                {event.evidencePacket && (
                  <span className="break-all">packet {event.evidencePacket}</span>
                )}
              </p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
