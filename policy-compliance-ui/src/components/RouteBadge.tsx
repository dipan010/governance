import { routeLabel } from "../lib/format";
import type { RoutePath } from "../types";

const ROUTE_CLASS: Record<RoutePath, string> = {
  source_pr_plus_change_ticket: "border-accent/45 bg-accent/12 text-accent",
  remediation_dry_run: "border-low/45 bg-low/12 text-low",
  owner_ticket_or_change_request: "border-medium/45 bg-medium/15 text-medium",
  time_bound_exception: "border-warning/45 bg-warning/15 text-warning",
  blocked_manual_review: "border-danger/45 bg-danger/12 text-danger",
  escalation: "border-high/45 bg-high/12 text-high",
  observe: "border-line bg-surface-sunken text-ink-muted",
  invalid_finding: "border-line bg-surface-sunken text-ink-muted",
};

export function RouteBadge({ route }: { route: RoutePath }) {
  return <span className={`chip ${ROUTE_CLASS[route]}`}>{routeLabel(route)}</span>;
}
