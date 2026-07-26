import type { RankMode } from "../types";

/**
 * The hero control: raw severity order versus the deterministic
 * agent ranking. The two orderings differ, which is the point.
 */
export function RankToggle({
  mode,
  onChange,
}: {
  mode: RankMode;
  onChange: (mode: RankMode) => void;
}) {
  const options: Array<{ value: RankMode; label: string; hint: string }> = [
    { value: "raw", label: "Raw severity order", hint: "Severity only" },
    { value: "ranked", label: "Agent-ranked order", hint: "Deterministic risk score" },
  ];

  return (
    <div
      role="group"
      aria-label="Worklist ordering"
      className="inline-flex overflow-hidden rounded-md border border-line"
    >
      {options.map((option) => {
        const active = option.value === mode;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            title={option.hint}
            onClick={() => onChange(option.value)}
            className={`px-3 py-1.5 text-sm font-medium transition-colors ${
              active
                ? "bg-accent text-white"
                : "bg-surface-raised text-ink-muted hover:bg-surface-sunken"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
