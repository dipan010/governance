import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type {
  Artifact,
  AuditEvent,
  DashboardSummary,
  SortMode,
  ViolationDetail,
  ViolationSummary,
} from "./api/types";
import { ComplianceSummary } from "./components/ComplianceSummary";
import { FindingCard } from "./components/FindingCard";
import { Worklist } from "./components/Worklist";

export default function App() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [violations, setViolations] = useState<ViolationSummary[]>([]);
  const [sort, setSort] = useState<SortMode>("ranked");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ViolationDetail | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    setSummary(await api.summary());
    setViolations(await api.violations(sort));
  }, [sort]);

  const refreshDetail = useCallback(async (id: string) => {
    setDetail(await api.violation(id));
    setArtifacts(await api.artifacts(id));
    setAudit(await api.audit(id));
  }, []);

  useEffect(() => {
    refreshList().catch((e) => setError(String(e)));
  }, [refreshList]);

  useEffect(() => {
    if (selectedId) {
      refreshDetail(selectedId).catch((e) => setError(String(e)));
    }
  }, [selectedId, refreshDetail]);

  const act = useCallback(
    async (action: () => Promise<unknown>) => {
      if (!selectedId) return;
      setBusy(true);
      setError(null);
      try {
        await action();
      } catch (e) {
        setError(errorMessage(e));
      } finally {
        setBusy(false);
        await refreshDetail(selectedId).catch(() => undefined);
        await refreshList().catch(() => undefined);
      }
    },
    [selectedId, refreshDetail, refreshList],
  );

  return (
    <main>
      <h1>Policy Compliance and Drift Detection</h1>
      <p className="scope">
        Subscription: ABI TECHOPS CLOUD ENGG · Resource group:
        ghq-3-squad3-cloudgov-dev-rg
      </p>
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}
      {summary ? <ComplianceSummary summary={summary} /> : null}
      <div className="layout">
        <Worklist
          violations={violations}
          sort={sort}
          onSortChange={setSort}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        {detail ? (
          <FindingCard
            detail={detail}
            artifacts={artifacts}
            audit={audit}
            busy={busy}
            onRequestApproval={() =>
              act(() => api.requestApproval(detail.violationId))
            }
            onDecideApproval={(decision, approver, reason) =>
              act(() => api.decideApproval(detail.violationId, decision, approver, reason))
            }
            onGenerateArtifacts={() =>
              act(() => api.generateArtifacts(detail.violationId))
            }
            onVerify={() => act(() => api.verify(detail.violationId))}
            onClose={() => act(() => api.close(detail.violationId))}
          />
        ) : (
          <p className="placeholder">Select a finding to open its card.</p>
        )}
      </div>
    </main>
  );
}

function errorMessage(e: unknown): string {
  if (e && typeof e === "object" && "body" in e) {
    const body = (e as { body: unknown }).body;
    if (body && typeof body === "object" && "detail" in body) {
      return JSON.stringify((body as { detail: unknown }).detail);
    }
  }
  return String(e);
}
