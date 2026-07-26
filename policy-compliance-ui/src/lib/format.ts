import type { RoutePath } from "../types";

/** Last segment of an Azure resource ID, for dense table cells. */
export function shortResourceId(resourceId: string): string {
  const parts = resourceId.split("/").filter(Boolean);
  return parts.at(-1) ?? resourceId;
}

/** "Microsoft.Storage/storageAccounts" → "storageAccounts". */
export function shortResourceType(resourceType: string): string {
  return resourceType.split("/").at(-1) ?? resourceType;
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

/** snake_case identifiers → "Sentence case" for display. */
export function humanize(token: string): string {
  const spaced = token.replace(/[_.]/g, " ").trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export const ROUTE_LABELS: Record<RoutePath, string> = {
  source_pr_plus_change_ticket: "Source PR + change ticket",
  remediation_dry_run: "Remediation dry-run",
  owner_ticket_or_change_request: "Owner ticket",
  time_bound_exception: "Time-bound exception",
  blocked_manual_review: "Blocked — manual review",
  escalation: "Escalation",
  observe: "Observe",
  invalid_finding: "Invalid finding",
};

export function routeLabel(route: RoutePath): string {
  return ROUTE_LABELS[route] ?? route;
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String(error);
}
