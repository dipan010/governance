import { Link, useParams } from "react-router-dom";
import { BlockerList } from "../components/BlockerList";
import { ErrorState } from "../components/ErrorState";
import { RiskBandBadge } from "../components/RiskBandBadge";
import { RouteBadge } from "../components/RouteBadge";
import { ScoreFactorChips } from "../components/ScoreFactorChips";
import { SkeletonCard } from "../components/Skeleton";
import { SourceMap } from "../components/SourceMap";
import { formatDateTime, humanize } from "../lib/format";
import { useViolation } from "../store/useViolations";

function Field({
  label,
  children,
  wide = false,
}: {
  label: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <dt className="label">{label}</dt>
      <dd className="value mt-0.5">{children}</dd>
    </div>
  );
}

function Panel({
  title,
  children,
  aside,
}: {
  title: string;
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  return (
    <section className="card card-pad flex flex-col gap-3" aria-label={title}>
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
        {aside}
      </header>
      {children}
    </section>
  );
}

export function ViolationDetail() {
  const { id = "" } = useParams();
  const { data, loading, error, reload } = useViolation(id);

  if (loading && !data) {
    return (
      <div className="flex flex-col gap-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (error && !data) {
    return <ErrorState message={error} onRetry={reload} />;
  }

  if (!data) {
    return <ErrorState message={`Finding ${id} was not found`} />;
  }

  const {
    policyEvidence,
    resourceFacts,
    riskSignals,
    ownership,
    decision,
    actionState,
    verification,
    history,
    missingEvidence,
  } = data;

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-semibold text-ink">
              {data.violationId}
            </h1>
            <RiskBandBadge band={decision.riskBand} score={decision.riskScore} />
            <RouteBadge route={decision.recommendedPath} />
            <span className="chip border-line bg-surface-sunken text-ink-muted">
              {actionState.actionStatus}
            </span>
          </div>
          <p className="mt-1 text-sm text-ink-muted">
            {policyEvidence.policyName}
          </p>
        </div>
        <div className="flex gap-2">
          <Link className="btn-secondary" to={`/violations/${id}/route`}>
            Route view
          </Link>
          <Link className="btn-secondary" to={`/violations/${id}/audit`}>
            Audit trail
          </Link>
        </div>
      </header>

      {missingEvidence.length > 0 && (
        <p
          role="status"
          className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger"
        >
          Missing evidence: {missingEvidence.map(humanize).join(", ")}
        </p>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Raw evidence">
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            <Field label="Compliance state">
              <span className="chip border-danger/40 bg-danger/10 text-danger">
                {policyEvidence.complianceState}
              </span>
            </Field>
            <Field label="Evaluated at">
              {formatDateTime(policyEvidence.evaluatedAt)}
            </Field>
            <Field label="Failure reason" wide>
              {policyEvidence.failureReason ?? "—"}
            </Field>
            <Field label="Policy">{policyEvidence.policyId}</Field>
            <Field label="Initiative">{policyEvidence.initiative ?? "—"}</Field>
            <Field label="Assignment">{policyEvidence.assignmentId ?? "—"}</Field>
            <Field label="Regulatory control">
              {riskSignals.regulatoryControl ?? "—"}
            </Field>
          </dl>
        </Panel>

        <Panel title="Enriched resource context">
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            <Field label="Resource ID" wide>
              <span className="mono break-all">{resourceFacts.resourceId}</span>
            </Field>
            <Field label="Type">{resourceFacts.resourceType}</Field>
            <Field label="Environment">{resourceFacts.environment}</Field>
            <Field label="Owner">
              {ownership.ownerTeam ? (
                <>
                  {ownership.ownerTeam}
                  <span className="ml-1 text-ink-subtle">
                    ({ownership.ownerEmail})
                  </span>
                </>
              ) : (
                <span className="chip border-danger/40 bg-danger/10 text-danger">
                  Owner gap — discovery required
                </span>
              )}
            </Field>
            <Field label="Business app">{ownership.businessApp ?? "—"}</Field>
            <Field label="Exposure">
              {riskSignals.internetExposure ? "Internet exposed" : "Private only"}
            </Field>
            <Field label="Data classification">
              {riskSignals.dataClassification}
            </Field>
            <Field label="Subscription">{resourceFacts.subscriptionId}</Field>
            <Field label="Resource group">{resourceFacts.resourceGroup}</Field>
          </dl>
        </Panel>

        <Panel
          title="Risk explanation"
          aside={
            <span className="chip border-line bg-surface-sunken text-ink-muted">
              Actionability {decision.actionabilityScore}
            </span>
          }
        >
          <div className="flex flex-wrap items-center gap-2">
            <RiskBandBadge band={decision.riskBand} score={decision.riskScore} />
            <span className="text-[13px] text-ink-subtle">
              rules {decision.scoreRuleVersion} · {decision.routeRuleVersion}
            </span>
          </div>
          <div>
            <p className="label mb-1.5">Score drivers</p>
            <ScoreFactorChips factors={decision.scoreFactors} />
          </div>
          <div>
            <p className="label mb-1.5">Blockers</p>
            <BlockerList blockers={decision.blockers} compact />
          </div>
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            <Field label="Owner confidence">{ownership.ownerConfidence}</Field>
            <Field label="Source confidence">{history.sourceConfidence}</Field>
            <Field label="Recurrence count">{history.recurrenceCount}</Field>
            <Field label="Previous fix">{history.previousFix ?? "none"}</Field>
          </dl>
        </Panel>

        <Panel title="Focused-agent signals">
          {riskSignals.focusedSignals.length === 0 ? (
            <p className="text-sm text-ink-muted">No domain signals emitted.</p>
          ) : (
            <ul className="flex flex-wrap gap-1.5">
              {riskSignals.focusedSignals.map((signal) => (
                <li
                  key={signal}
                  className="chip border-accent/30 bg-accent-soft font-mono text-accent"
                >
                  {signal}
                </li>
              ))}
            </ul>
          )}
          <p className="text-[13px] text-ink-subtle">
            Focused agents emit signals only. The central scorer owns the score
            and the routing planner owns the route.
          </p>
        </Panel>

        <Panel title="Source map">
          <SourceMap
            ownership={ownership}
            entries={data.sourceMap}
            sourceDriftLikely={history.sourceDriftLikely}
          />
        </Panel>

        <Panel
          title="Recommended route"
          aside={<RouteBadge route={decision.recommendedPath} />}
        >
          <p className="value">{decision.routeReason}</p>
          <div>
            <p className="label mb-1">Side effects</p>
            <ul className="flex flex-wrap gap-1.5">
              {decision.sideEffects.map((effect) => (
                <li
                  key={effect}
                  className="chip border-line bg-surface-sunken text-ink-muted"
                >
                  {effect}
                </li>
              ))}
            </ul>
          </div>
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            <Field label="Approval required">
              {decision.approvalRequired ? "Yes" : "No"}
            </Field>
            <Field label="Approval state">{actionState.approvalState}</Field>
            <Field label="Approver role">{decision.approverRole ?? "—"}</Field>
            <Field label="Ticket">{actionState.ticketId ?? "—"}</Field>
            <Field label="Rollback / next action" wide>
              {decision.rollbackOrNextAction}
            </Field>
          </dl>
          <Link className="btn-primary self-start" to={`/violations/${id}/route`}>
            Open route view
          </Link>
        </Panel>

        <Panel
          title="Verification"
          aside={
            <span
              className={`chip ${
                verification.verificationResult === "Compliant"
                  ? "border-success/40 bg-success/10 text-success"
                  : "border-line bg-surface-sunken text-ink-muted"
              }`}
            >
              {verification.verificationResult}
            </span>
          }
        >
          <div>
            <p className="label">Verification query</p>
            <pre className="pre-block mt-1 whitespace-pre-wrap">
              {verification.verificationQuery}
            </pre>
          </div>
          <Field label="Expected compliant value">
            <span className="mono">{verification.expectedCompliantValue}</span>
          </Field>
          <Field label="Next action">{verification.nextAction}</Field>
        </Panel>
      </div>
    </div>
  );
}
