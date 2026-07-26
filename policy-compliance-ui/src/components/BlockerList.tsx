import { humanize } from "../lib/format";

/** Blockers are first-class information, never a hidden warning. */
export function BlockerList({
  blockers,
  compact = false,
}: {
  blockers: string[];
  compact?: boolean;
}) {
  if (blockers.length === 0) {
    return (
      <span className="chip border-low/40 bg-low/10 text-low">No blockers</span>
    );
  }
  return (
    <ul className={compact ? "flex flex-wrap gap-1" : "flex flex-col gap-1"}>
      {blockers.map((blocker) => (
        <li
          key={blocker}
          className="chip border-danger/40 bg-danger/10 text-danger"
        >
          <span aria-hidden="true">■</span>
          {humanize(blocker)}
        </li>
      ))}
    </ul>
  );
}
