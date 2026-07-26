import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApprovalCard } from "../components/ApprovalCard";
import { ArtifactPreview } from "../components/ArtifactPreview";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { RouteBadge } from "../components/RouteBadge";
import { SkeletonCard } from "../components/Skeleton";
import { VerificationPanel } from "../components/VerificationPanel";
import { routeLabel } from "../lib/format";
import { useViolation } from "../store/useViolations";
import type { ApprovalPayload, Artifact } from "../types";

export function RouteView() {
  const { id = "" } = useParams();
  const {
    data,
    loading,
    error,
    reload,
    busy,
    requestApproval,
    decide,
    generateArtifact,
    runVerification,
  } = useViolation(id);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [approvalPayload, setApprovalPayload] = useState<ApprovalPayload | null>(
    null,
  );

  if (loading && !data) return <SkeletonCard />;
  if (error && !data) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <ErrorState message={`Finding ${id} was not found`} />;

  const { decision, actionState } = data;
  const approvalReady =
    !decision.approvalRequired || actionState.approvalState === "Approved";

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-semibold text-ink">
              {data.violationId} — route
            </h1>
            <RouteBadge route={decision.recommendedPath} />
          </div>
          <p className="mt-1 text-sm text-ink-muted">{decision.routeReason}</p>
        </div>
        <div className="flex gap-2">
          <Link className="btn-secondary" to={`/violations/${id}`}>
            Finding card
          </Link>
          <Link className="btn-secondary" to={`/violations/${id}/audit`}>
            Audit trail
          </Link>
        </div>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        <div className="flex flex-col gap-4">
          <ApprovalCard
            violation={data}
            payload={approvalPayload}
            busy={busy}
            onRequest={async () => {
              const payload = await requestApproval();
              if (payload) setApprovalPayload(payload);
            }}
            onDecide={(nextDecision) => {
              void decide(nextDecision);
            }}
          />

          <section
            className="card card-pad flex flex-col gap-3"
            aria-label="Route artifact"
          >
            <header className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-ink">
                {routeLabel(decision.recommendedPath)} artifact
              </h2>
              <button
                type="button"
                className="btn-primary"
                disabled={busy || !approvalReady}
                title={
                  approvalReady
                    ? undefined
                    : "Approval is required before this artifact can be generated"
                }
                onClick={async () => {
                  const generated = await generateArtifact();
                  if (generated) setArtifact(generated);
                }}
              >
                Generate artifact
              </button>
            </header>
            {!approvalReady && (
              <p className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
                Disabled until an approval is granted — changing actions never
                run ahead of a human decision.
              </p>
            )}
            {artifact ? (
              <p className="text-[13px] text-ink-subtle">
                Draft generated. It appears alongside this panel — nothing was
                sent to GitHub, ServiceNow, Jira, or Azure.
              </p>
            ) : (
              <p className="text-[13px] text-ink-subtle">
                One artifact is shown at a time, matching this finding&apos;s route.
              </p>
            )}
          </section>

          <VerificationPanel
            verification={data.verification}
            busy={busy}
            onVerify={() => {
              void runVerification();
            }}
          />
        </div>

        <div className="flex flex-col gap-4">
          {artifact ? (
            <ArtifactPreview artifact={artifact} />
          ) : (
            <EmptyState
              title="No artifact generated yet"
              description={
                approvalReady
                  ? "Generate the artifact for this route to preview the exact ticket, PR comment, dry-run plan, exception request, or blocked card."
                  : "Request and grant approval first; the artifact button unlocks once the approval is recorded."
              }
            />
          )}
        </div>
      </div>
    </div>
  );
}
