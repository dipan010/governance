import { formatDateTime, humanize } from "../lib/format";
import type { Artifact } from "../types";

/** Colored unified-diff rendering for PR previews. */
function DiffBody({ body }: { body: string }) {
  return (
    <pre className="pre-block">
      {body.split("\n").map((line, index) => {
        const tone = line.startsWith("+")
          ? "text-success"
          : line.startsWith("-")
            ? "text-danger"
            : line.startsWith("@@")
              ? "text-accent"
              : "text-ink-muted";
        return (
          <div key={index} className={tone}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}

export function ArtifactPreview({ artifact }: { artifact: Artifact }) {
  const isDiff = artifact.kind === "pr_comment_preview";

  return (
    <section
      className="card card-pad flex flex-col gap-3"
      aria-label={`Artifact ${artifact.kind}`}
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-ink">{artifact.title}</h2>
          <p className="mt-0.5 text-[11px] text-ink-subtle">
            {humanize(artifact.kind)} · generated{" "}
            {formatDateTime(artifact.createdAt)}
          </p>
        </div>
        {artifact.isDraft && (
          <span className="chip border-warning/40 bg-warning/10 text-warning">
            Draft — nothing is sent externally
          </span>
        )}
      </header>

      {isDiff ? <DiffBody body={artifact.body} /> : (
        <pre className="pre-block whitespace-pre-wrap">{artifact.body}</pre>
      )}
    </section>
  );
}
