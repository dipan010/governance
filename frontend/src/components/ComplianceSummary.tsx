import type { DashboardSummary } from "../api/types";

const METRICS: Array<{ key: keyof DashboardSummary; label: string }> = [
  { key: "totalFindings", label: "Total findings" },
  { key: "criticalFindings", label: "Critical" },
  { key: "repeatViolations", label: "Repeat violations" },
  { key: "autoRemediable", label: "Auto-remediable" },
  { key: "tickets", label: "Tickets" },
  { key: "prComments", label: "PR/comments" },
  { key: "exceptions", label: "Exceptions" },
  { key: "blockedUnsafeActions", label: "Blocked unsafe actions" },
  { key: "verifiedFixes", label: "Verified fixes" },
];

export function ComplianceSummary({ summary }: { summary: DashboardSummary }) {
  return (
    <section className="summary" aria-label="Compliance summary">
      {METRICS.map(({ key, label }) => (
        <div className="metric" key={key}>
          <span className="metric-value">{summary[key]}</span>
          <span className="metric-label">{label}</span>
        </div>
      ))}
    </section>
  );
}
