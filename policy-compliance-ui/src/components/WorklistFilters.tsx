import { humanize, routeLabel } from "../lib/format";
import type { RoutePath, Violation, WorklistFilters } from "../types";

type FilterKey = keyof WorklistFilters;

function unique(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.filter((v): v is string => Boolean(v)))].sort();
}

export function WorklistFiltersBar({
  violations,
  filters,
  onChange,
  onReset,
}: {
  violations: Violation[];
  filters: WorklistFilters;
  onChange: (key: FilterKey, value: string) => void;
  onReset: () => void;
}) {
  const definitions: Array<{
    key: FilterKey;
    label: string;
    options: string[];
    render?: (value: string) => string;
  }> = [
    {
      key: "policy",
      label: "Policy",
      options: unique(violations.map((v) => v.policyEvidence.policyId)),
    },
    {
      key: "severity",
      label: "Severity",
      options: unique(violations.map((v) => v.riskSignals.severity)),
    },
    {
      key: "riskBand",
      label: "Risk band",
      options: unique(violations.map((v) => v.decision.riskBand)),
    },
    {
      key: "exposure",
      label: "Exposure",
      options: unique(
        violations.map((v) =>
          v.riskSignals.internetExposure ? "internet exposed" : "private only",
        ),
      ),
    },
    {
      key: "dataClassification",
      label: "Data class",
      options: unique(violations.map((v) => v.riskSignals.dataClassification)),
    },
    {
      key: "owner",
      label: "Owner",
      options: unique(
        violations.map((v) => v.ownership.ownerTeam ?? "Owner gap"),
      ),
    },
    {
      key: "app",
      label: "App",
      options: unique(violations.map((v) => v.ownership.businessApp)),
    },
    {
      key: "sourceDrift",
      label: "Source drift",
      options: unique(
        violations.map((v) => String(v.history.sourceDriftLikely)),
      ),
    },
    {
      key: "route",
      label: "Route",
      options: unique(violations.map((v) => v.decision.recommendedPath)),
      render: (value) => routeLabel(value as RoutePath),
    },
    {
      key: "confidence",
      label: "Confidence",
      options: unique(violations.map((v) => v.ownership.ownerConfidence)),
    },
    {
      key: "status",
      label: "Status",
      options: unique(violations.map((v) => v.actionState.actionStatus)),
    },
    {
      key: "blocker",
      label: "Blocker",
      options: unique(violations.flatMap((v) => v.decision.blockers)),
      render: humanize,
    },
  ];

  const activeCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-end gap-2">
        {definitions.map(({ key, label, options, render }) => (
          <label key={key} className="flex flex-col gap-1">
            <span className="label">{label}</span>
            <select
              className="field min-w-[8.5rem]"
              aria-label={`Filter by ${label.toLowerCase()}`}
              value={filters[key] ?? ""}
              onChange={(event) => onChange(key, event.target.value)}
            >
              <option value="">All</option>
              {options.map((option) => (
                <option key={option} value={option}>
                  {render ? render(option) : option}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      {activeCount > 0 && (
        <div>
          <button type="button" className="btn-secondary" onClick={onReset}>
            Clear {activeCount} filter{activeCount === 1 ? "" : "s"}
          </button>
        </div>
      )}
    </div>
  );
}
