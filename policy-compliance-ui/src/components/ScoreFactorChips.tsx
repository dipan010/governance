import type { ScoreFactor } from "../types";

/**
 * Renders the drivers the server used. Points are displayed, never summed
 * or recomputed here — scoring is a backend responsibility.
 */
export function ScoreFactorChips({ factors }: { factors: ScoreFactor[] }) {
  if (factors.length === 0) {
    return <p className="text-sm text-ink-muted">No scoring drivers recorded.</p>;
  }
  return (
    <ul className="flex flex-wrap gap-1.5">
      {factors.map((factor) => (
        <li
          key={factor.label}
          className="chip border-accent/30 bg-accent-soft text-accent"
        >
          {factor.label}
          <span className="font-semibold tabular-nums">+{factor.points}</span>
        </li>
      ))}
    </ul>
  );
}
