import { useCallback, useEffect, useState } from "react";
import { dataClient } from "../data/dataClient";
import { errorMessage } from "../lib/format";
import type {
  ApprovalDecision,
  ApprovalPayload,
  Artifact,
  AuditEvent,
  DashboardSummary,
  Violation,
  WorklistFilters,
} from "../types";
import { pushToast } from "./useToast";

/**
 * Session cache shared by every screen, so navigating between the worklist,
 * a finding card, its route view, and its audit trail keeps state without
 * refetching or losing an approval that was just granted.
 */
const violationCache = new Map<string, Violation>();
let listCache: Violation[] | null = null;
const cacheListeners = new Set<() => void>();

function notifyCacheChanged(): void {
  for (const listener of cacheListeners) listener();
}

function cacheViolation(violation: Violation): void {
  violationCache.set(violation.violationId, violation);
  if (listCache) {
    listCache = listCache.map((v) =>
      v.violationId === violation.violationId ? violation : v,
    );
  }
  notifyCacheChanged();
}

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/** Generic async loader with loading, error, and manual retry. */
function useAsync<T>(
  loader: () => Promise<T>,
  deps: React.DependencyList,
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    loader()
      .then((value) => {
        if (!cancelled) setData(value);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(errorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { data, loading, error, reload };
}

export function useWorklist(filters: WorklistFilters = {}): AsyncState<
  Violation[]
> {
  const key = JSON.stringify(filters);
  const state = useAsync<Violation[]>(async () => {
    const list = await dataClient.listViolations(filters);
    listCache = list;
    for (const violation of list) violationCache.set(violation.violationId, violation);
    return list;
  }, [key]);
  return state;
}

export function useDashboardSummary(): AsyncState<DashboardSummary> {
  return useAsync<DashboardSummary>(() => dataClient.dashboardSummary(), []);
}

export interface ViolationState extends AsyncState<Violation> {
  busy: boolean;
  requestApproval: () => Promise<ApprovalPayload | null>;
  decide: (decision: ApprovalDecision) => Promise<void>;
  generateArtifact: () => Promise<Artifact | null>;
  runVerification: () => Promise<void>;
}

export function useViolation(id: string): ViolationState {
  const [busy, setBusy] = useState(false);
  const state = useAsync<Violation>(async () => {
    const cached = violationCache.get(id);
    if (cached) return cached;
    const violation = await dataClient.getViolation(id);
    violationCache.set(id, violation);
    return violation;
  }, [id]);

  const [, forceRender] = useState(0);
  useEffect(() => {
    const listener = () => forceRender((n) => n + 1);
    cacheListeners.add(listener);
    return () => {
      cacheListeners.delete(listener);
    };
  }, []);

  const refresh = useCallback(async () => {
    const fresh = await dataClient.getViolation(id);
    cacheViolation(fresh);
    state.reload();
  }, [id, state]);

  const run = useCallback(
    async <T,>(
      action: () => Promise<T>,
      successMessage: string,
    ): Promise<T | null> => {
      setBusy(true);
      try {
        const result = await action();
        await refresh();
        pushToast("success", successMessage);
        return result;
      } catch (err: unknown) {
        pushToast("error", errorMessage(err));
        return null;
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  const requestApproval = useCallback(
    () =>
      run(
        () => dataClient.requestApproval(id),
        `Approval requested for ${id}`,
      ),
    [id, run],
  );

  const decide = useCallback(
    async (decision: ApprovalDecision) => {
      await run(
        () => dataClient.approve(id, decision),
        decision.decision === "approve"
          ? `${id} approved by ${decision.approver}`
          : `${id} rejected — reason recorded`,
      );
    },
    [id, run],
  );

  const generateArtifact = useCallback(
    () =>
      run(
        () => dataClient.generateArtifact(id),
        `Draft artifact generated for ${id}`,
      ),
    [id, run],
  );

  const runVerification = useCallback(async () => {
    await run(
      () => dataClient.verify(id),
      `Verification complete for ${id}`,
    );
  }, [id, run]);

  const data = violationCache.get(id) ?? state.data;

  return {
    ...state,
    data,
    busy,
    requestApproval,
    decide,
    generateArtifact,
    runVerification,
  };
}

export function useAuditTrail(id: string): AsyncState<AuditEvent[]> {
  return useAsync<AuditEvent[]>(() => dataClient.auditTrail(id), [id]);
}
