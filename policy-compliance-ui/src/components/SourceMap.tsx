import type { Ownership, SourceMapEntry } from "../types";

export function SourceMap({
  ownership,
  entries,
  sourceDriftLikely,
}: {
  ownership: Ownership;
  entries: SourceMapEntry[];
  sourceDriftLikely: boolean;
}) {
  if (!ownership.repoPath) {
    return (
      <p className="text-sm text-ink-muted">
        No IaC mapping for this resource, so a source fix cannot be proposed.
        Runtime remediation would be the only option once an owner is known.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
        <div>
          <dt className="label">Repository</dt>
          <dd className="value">
            <a
              className="text-accent underline underline-offset-2"
              href={ownership.repoUrl ?? "#"}
              target="_blank"
              rel="noreferrer"
            >
              {ownership.repoUrl}
            </a>
          </dd>
        </div>
        <div>
          <dt className="label">CODEOWNER</dt>
          <dd className="value">{ownership.codeOwner ?? "unknown"}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="label">File</dt>
          <dd className="mono text-ink">{ownership.repoPath}</dd>
        </div>
      </dl>

      {entries.length > 0 && (
        <div className="table-scroll rounded-md border border-line">
          <table className="w-full min-w-[34rem] border-collapse text-sm">
            <thead>
              <tr className="bg-surface-sunken text-left">
                {["Source property", "Current", "Expected", "Runtime property"].map(
                  (heading) => (
                    <th
                      key={heading}
                      scope="col"
                      className="border-b border-line px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-subtle"
                    >
                      {heading}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => {
                const drifted = entry.currentValue !== entry.expectedValue;
                return (
                  <tr key={entry.property} className="border-b border-line last:border-0">
                    <td className="mono px-3 py-2 text-ink">{entry.property}</td>
                    <td
                      className={`mono px-3 py-2 ${drifted ? "text-danger" : "text-ink-muted"}`}
                    >
                      {entry.currentValue}
                    </td>
                    <td className="mono px-3 py-2 text-success">
                      {entry.expectedValue}
                    </td>
                    <td className="mono px-3 py-2 text-ink-muted">
                      {entry.runtimeProperty}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {sourceDriftLikely && (
        <p className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
          A runtime-only patch would be <strong>temporary</strong>: the source
          still contains the non-compliant value, so the next deployment
          reintroduces this violation.
        </p>
      )}
    </div>
  );
}
