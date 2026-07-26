import { useMemo, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { RankToggle } from "../components/RankToggle";
import { SkeletonTable } from "../components/Skeleton";
import { WorklistFiltersBar } from "../components/WorklistFilters";
import { WorklistTable } from "../components/WorklistTable";
import { useWorklist } from "../store/useViolations";
import type { RankMode, Severity, Violation, WorklistFilters } from "../types";

const SEVERITY_RANK: Record<Severity, number> = {
  Critical: 4,
  High: 3,
  Medium: 2,
  Low: 1,
  Unknown: 0,
};

/**
 * Ordering is a display concern only — the scores themselves come from the
 * server's deterministic scorer and are never recomputed here.
 */
function order(violations: Violation[], mode: RankMode): Violation[] {
  const sorted = [...violations];
  if (mode === "raw") {
    sorted.sort((a, b) => {
      const diff =
        SEVERITY_RANK[b.riskSignals.severity] -
        SEVERITY_RANK[a.riskSignals.severity];
      return diff !== 0 ? diff : a.violationId.localeCompare(b.violationId);
    });
  } else {
    sorted.sort((a, b) => {
      const diff = b.decision.riskScore - a.decision.riskScore;
      return diff !== 0 ? diff : a.violationId.localeCompare(b.violationId);
    });
  }
  return sorted;
}

export function Worklist() {
  const [mode, setMode] = useState<RankMode>("ranked");
  const [filters, setFilters] = useState<WorklistFilters>({});
  const { data, loading, error, reload } = useWorklist(filters);

  const ordered = useMemo(() => order(data ?? [], mode), [data, mode]);

  const changeFilter = (key: keyof WorklistFilters, value: string) =>
    setFilters((current) => {
      const next = { ...current };
      if (value) next[key] = value;
      else delete next[key];
      return next;
    });

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-ink">Worklist</h1>
          <p className="text-sm text-ink-muted">
            {mode === "ranked"
              ? "Ordered by the agent's deterministic risk score."
              : "Ordered by raw policy severity alone."}
          </p>
        </div>
        <RankToggle mode={mode} onChange={setMode} />
      </header>

      {data && data.length > 0 && (
        <WorklistFiltersBar
          violations={data}
          filters={filters}
          onChange={changeFilter}
          onReset={() => setFilters({})}
        />
      )}

      {loading && <SkeletonTable rows={5} />}

      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && ordered.length === 0 && (
        <EmptyState
          title="No findings match these filters"
          description="Clear one or more filters to widen the worklist."
          action={
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setFilters({})}
            >
              Clear filters
            </button>
          }
        />
      )}

      {!loading && !error && ordered.length > 0 && (
        <>
          <WorklistTable violations={ordered} />
          <p className="text-[13px] text-ink-subtle">
            Showing {ordered.length} finding{ordered.length === 1 ? "" : "s"}.
            Switch the ordering to compare raw severity against the agent's
            ranking — the top of the list changes.
          </p>
        </>
      )}
    </div>
  );
}
