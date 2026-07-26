import { useNavigate } from "react-router-dom";
import { shortResourceId, shortResourceType } from "../lib/format";
import type { Violation } from "../types";
import { BlockerList } from "./BlockerList";
import { RiskBandBadge } from "./RiskBandBadge";
import { RouteBadge } from "./RouteBadge";

export function WorklistTable({ violations }: { violations: Violation[] }) {
  const navigate = useNavigate();

  const open = (id: string) => navigate(`/violations/${id}`);

  return (
    <div className="table-scroll rounded-lg border border-line">
      <table className="w-full min-w-[68rem] border-collapse text-sm [&_td]:align-top">
        <caption className="sr-only">
          Governance findings ordered by the selected ranking mode
        </caption>
        <thead>
          <tr className="bg-surface-sunken text-left">
            {[
              "Violation",
              "Policy",
              "Resource",
              "Owner",
              "Risk",
              "Blockers",
              "Route",
              "Status",
            ].map((heading) => (
              <th
                key={heading}
                scope="col"
                className="whitespace-nowrap border-b border-line px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-subtle"
              >
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {violations.map((violation) => {
            const { ownership, resourceFacts, decision, actionState } = violation;
            return (
              <tr
                key={violation.violationId}
                tabIndex={0}
                role="link"
                aria-label={`Open finding ${violation.violationId}`}
                onClick={() => open(violation.violationId)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    open(violation.violationId);
                  }
                }}
                className="cursor-pointer border-b border-line last:border-0 hover:bg-accent-soft/60 focus:bg-accent-soft/60"
              >
                <td className="px-3 py-2.5 font-semibold text-accent">
                  {violation.violationId}
                </td>
                <td className="w-[15rem] max-w-[15rem] px-3 py-2.5">
                  <span
                    className="block truncate"
                    title={violation.policyEvidence.policyName}
                  >
                    {violation.policyEvidence.policyName}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <span className="mono block text-ink">
                    {shortResourceId(resourceFacts.resourceId)}
                  </span>
                  <span className="text-[11px] text-ink-subtle">
                    {shortResourceType(resourceFacts.resourceType)} ·{" "}
                    {resourceFacts.environment}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5">
                  {ownership.ownerTeam ? (
                    <span className="text-ink">{ownership.ownerTeam}</span>
                  ) : (
                    <span className="chip border-danger/40 bg-danger/10 text-danger">
                      Owner gap
                    </span>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5">
                  <RiskBandBadge band={decision.riskBand} score={decision.riskScore} />
                </td>
                <td className="min-w-[14.5rem] px-3 py-2.5">
                  <BlockerList blockers={decision.blockers} compact />
                </td>
                <td className="whitespace-nowrap px-3 py-2.5">
                  <RouteBadge route={decision.recommendedPath} />
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-ink-muted">
                  {actionState.actionStatus}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
