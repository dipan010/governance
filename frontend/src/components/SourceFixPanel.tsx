import type { Evidence } from "../api/types";

export function SourceFixPanel({ evidence }: { evidence: Evidence }) {
  const { ownership, history } = evidence;
  if (!ownership.repoPath) {
    return (
      <section aria-label="Source fix" className="panel">
        <h3>Source fix</h3>
        <p>No IaC mapping for this resource (source confidence: {history.sourceConfidence}).</p>
      </section>
    );
  }
  return (
    <section aria-label="Source fix" className="panel">
      <h3>Source fix</h3>
      <p>
        Repo:{" "}
        <a href={ownership.repoUrl ?? "#"} rel="noreferrer" target="_blank">
          {ownership.repoUrl}
        </a>
      </p>
      <p>
        File: <code>{ownership.repoPath}</code>
      </p>
      <p>CODEOWNER: {ownership.codeOwner ?? "unknown"}</p>
      <p>
        Source drift likely:{" "}
        <strong>{String(history.sourceDriftLikely ?? "unknown")}</strong> (confidence:{" "}
        {history.sourceConfidence})
      </p>
      {history.sourceDriftLikely ? (
        <p className="warning">
          Runtime-only patching would be temporary: the source still contains the
          non-compliant value.
        </p>
      ) : null}
    </section>
  );
}
