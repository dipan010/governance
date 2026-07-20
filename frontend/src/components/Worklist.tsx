import { useMemo, useState } from "react";
import type { SortMode, ViolationSummary } from "../api/types";

export interface WorklistFilters {
  policy: string;
  severity: string;
  exposure: string;
  dataClassification: string;
  owner: string;
  app: string;
  sourceDrift: string;
  route: string;
  confidence: string;
  status: string;
  blocker: string;
}

const EMPTY_FILTERS: WorklistFilters = {
  policy: "",
  severity: "",
  exposure: "",
  dataClassification: "",
  owner: "",
  app: "",
  sourceDrift: "",
  route: "",
  confidence: "",
  status: "",
  blocker: "",
};

function options(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.filter((v): v is string => Boolean(v)))].sort();
}

export function Worklist({
  violations,
  sort,
  onSortChange,
  selectedId,
  onSelect,
}: {
  violations: ViolationSummary[];
  sort: SortMode;
  onSortChange: (sort: SortMode) => void;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [filters, setFilters] = useState<WorklistFilters>(EMPTY_FILTERS);

  const filtered = useMemo(
    () =>
      violations.filter((v) => {
        if (filters.policy && v.policyId !== filters.policy) return false;
        if (filters.severity && v.severity !== filters.severity) return false;
        if (filters.exposure && v.exposure !== filters.exposure) return false;
        if (
          filters.dataClassification &&
          v.dataClassification !== filters.dataClassification
        )
          return false;
        if (filters.owner && (v.ownerTeam ?? "(none)") !== filters.owner)
          return false;
        if (filters.app && v.businessApp !== filters.app) return false;
        if (
          filters.sourceDrift &&
          String(v.sourceDriftLikely ?? "unknown") !== filters.sourceDrift
        )
          return false;
        if (filters.route && v.route !== filters.route) return false;
        if (filters.confidence && v.ownerConfidence !== filters.confidence)
          return false;
        if (filters.status && v.actionStatus !== filters.status) return false;
        if (filters.blocker && !v.blockers.includes(filters.blocker)) return false;
        return true;
      }),
    [violations, filters],
  );

  const set = (key: keyof WorklistFilters) => (value: string) =>
    setFilters((f) => ({ ...f, [key]: value }));

  const filterDefs: Array<{
    key: keyof WorklistFilters;
    label: string;
    values: string[];
  }> = [
    { key: "policy", label: "Policy", values: options(violations.map((v) => v.policyId)) },
    { key: "severity", label: "Severity", values: options(violations.map((v) => v.severity)) },
    { key: "exposure", label: "Exposure", values: options(violations.map((v) => v.exposure)) },
    {
      key: "dataClassification",
      label: "Data classification",
      values: options(violations.map((v) => v.dataClassification)),
    },
    {
      key: "owner",
      label: "Owner",
      values: options(violations.map((v) => v.ownerTeam ?? "(none)")),
    },
    { key: "app", label: "App", values: options(violations.map((v) => v.businessApp)) },
    {
      key: "sourceDrift",
      label: "Source drift",
      values: options(violations.map((v) => String(v.sourceDriftLikely ?? "unknown"))),
    },
    { key: "route", label: "Route", values: options(violations.map((v) => v.route)) },
    {
      key: "confidence",
      label: "Confidence",
      values: options(violations.map((v) => v.ownerConfidence)),
    },
    { key: "status", label: "Status", values: options(violations.map((v) => v.actionStatus)) },
    { key: "blocker", label: "Blocker", values: options(violations.flatMap((v) => v.blockers)) },
  ];

  return (
    <section className="worklist" aria-label="Worklist">
      <div className="worklist-header">
        <h2>Worklist</h2>
        <div role="group" aria-label="Sort order" className="sort-toggle">
          <button
            className={sort === "raw" ? "active" : ""}
            onClick={() => onSortChange("raw")}
          >
            Raw severity
          </button>
          <button
            className={sort === "ranked" ? "active" : ""}
            onClick={() => onSortChange("ranked")}
          >
            Agent-ranked
          </button>
        </div>
      </div>
      <div className="filters">
        {filterDefs.map(({ key, label, values }) => (
          <label key={key}>
            {label}
            <select
              value={filters[key]}
              onChange={(e) => set(key)(e.target.value)}
              aria-label={`Filter by ${label.toLowerCase()}`}
            >
              <option value="">All</option>
              {values.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Policy</th>
            <th>Severity</th>
            <th>Score</th>
            <th>Band</th>
            <th>Actionability</th>
            <th>Route</th>
            <th>Blockers</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((v) => (
            <tr
              key={v.violationId}
              className={v.violationId === selectedId ? "selected" : ""}
              onClick={() => onSelect(v.violationId)}
            >
              <td>
                <button className="link" onClick={() => onSelect(v.violationId)}>
                  {v.violationId}
                </button>
              </td>
              <td>{v.policyName ?? v.policyId}</td>
              <td>{v.severity}</td>
              <td>{v.riskScore ?? "–"}</td>
              <td>
                <span className={`band band-${(v.riskBand ?? "none").toLowerCase()}`}>
                  {v.riskBand ?? "–"}
                </span>
              </td>
              <td>{v.actionabilityScore ?? "–"}</td>
              <td>{v.route ?? "unrouted"}</td>
              <td className="blockers-cell">
                {v.blockers.length ? v.blockers.join(", ") : "none"}
              </td>
              <td>{v.actionStatus}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
