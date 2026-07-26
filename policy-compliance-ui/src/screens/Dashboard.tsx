import { Link } from "react-router-dom";
import { BlockerList } from "../components/BlockerList";
import { ErrorState } from "../components/ErrorState";
import { RiskBandBadge } from "../components/RiskBandBadge";
import { RouteBadge } from "../components/RouteBadge";
import { Skeleton, StatTileSkeleton } from "../components/Skeleton";
import { StatTile } from "../components/StatTile";
import { useDashboardSummary } from "../store/useViolations";

export function Dashboard() {
  const { data, loading, error, reload } = useDashboardSummary();

  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        <StatTileSkeleton />
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-56 w-full" />
          <Skeleton className="h-56 w-full" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return <ErrorState message={error ?? "No summary available"} onRetry={reload} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <section aria-label="Compliance summary" className="flex flex-col gap-3">
        <h1 className="text-lg font-semibold text-ink">Compliance summary</h1>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9">
          <StatTile label="Total findings" value={data.totalFindings} />
          <StatTile
            label="Critical findings"
            value={data.criticalFindings}
            tone="critical"
          />
          <StatTile label="Repeat violations" value={data.repeatViolations} />
          <StatTile label="Auto-remediable" value={data.autoRemediable} />
          <StatTile label="Tickets" value={data.tickets} />
          <StatTile label="PRs / comments" value={data.prComments} />
          <StatTile label="Exceptions" value={data.exceptions} tone="warning" />
          <StatTile
            label="Blocked unsafe actions"
            value={data.blockedUnsafeActions}
            tone="warning"
          />
          <StatTile
            label="Verified fixes"
            value={data.verifiedFixes}
            tone="success"
          />
        </div>
      </section>

      <section aria-label="Risk versus actionability" className="flex flex-col gap-3">
        <div>
          <h2 className="text-base font-semibold text-ink">
            Risk vs actionability
          </h2>
          <p className="text-sm text-ink-muted">
            Risk and actionability are separate views. A Critical finding can
            still be blocked — those items need evidence, not automation.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card card-pad flex flex-col gap-3">
            <header className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-ink">
                High risk &amp; actionable
              </h3>
              <span className="chip border-success/40 bg-success/10 text-success">
                {data.highRiskActionable.length} ready to act
              </span>
            </header>
            {data.highRiskActionable.length === 0 ? (
              <p className="text-sm text-ink-muted">
                Nothing high-risk is currently actionable.
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {data.highRiskActionable.map((item) => (
                  <li
                    key={item.violationId}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-line px-3 py-2"
                  >
                    <div className="min-w-0">
                      <Link
                        to={`/violations/${item.violationId}`}
                        className="text-sm font-semibold text-accent underline-offset-2 hover:underline"
                      >
                        {item.violationId}
                      </Link>
                      <p className="truncate text-[13px] text-ink-muted">
                        {item.policyName}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-1.5">
                      <RiskBandBadge band={item.riskBand} score={item.riskScore} />
                      <RouteBadge route={item.route} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card card-pad flex flex-col gap-3">
            <header className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-ink">
                High risk but blocked
              </h3>
              <span className="chip border-danger/40 bg-danger/10 text-danger">
                {data.highRiskBlocked.length} need evidence
              </span>
            </header>
            {data.highRiskBlocked.length === 0 ? (
              <p className="text-sm text-ink-muted">
                No high-risk findings are blocked.
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {data.highRiskBlocked.map((item) => (
                  <li
                    key={item.violationId}
                    className="flex flex-col gap-1.5 rounded-md border border-line px-3 py-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="min-w-0">
                        <Link
                          to={`/violations/${item.violationId}`}
                          className="text-sm font-semibold text-accent underline-offset-2 hover:underline"
                        >
                          {item.violationId}
                        </Link>
                        <p className="truncate text-[13px] text-ink-muted">
                          {item.policyName}
                        </p>
                      </div>
                      <RiskBandBadge band={item.riskBand} score={item.riskScore} />
                    </div>
                    <BlockerList blockers={item.blockers} compact />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      <section className="card card-pad">
        <h2 className="section-title">How to read this console</h2>
        <ol className="mt-2 flex list-decimal flex-col gap-1 pl-5 text-sm text-ink-muted">
          <li>Findings are ingested and normalized into one violation model.</li>
          <li>
            A deterministic scorer re-ranks them differently from raw severity —
            see the{" "}
            <Link to="/worklist" className="text-accent underline underline-offset-2">
              worklist toggle
            </Link>
            .
          </li>
          <li>Each finding gets the safest available route.</li>
          <li>Changing actions require approval with side effects and rollback shown.</li>
          <li>Nothing closes without before/after proof and an audit packet.</li>
        </ol>
      </section>
    </div>
  );
}
