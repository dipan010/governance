export function StatTile({
  label,
  value,
  tone = "neutral",
  hint,
}: {
  label: string;
  value: number | string;
  tone?: "neutral" | "critical" | "warning" | "success";
  hint?: string;
}) {
  const toneClass = {
    neutral: "text-ink",
    critical: "text-critical",
    warning: "text-warning",
    success: "text-success",
  }[tone];

  return (
    <div className="card card-pad flex flex-col gap-0.5">
      <span className={`text-2xl font-semibold tabular-nums ${toneClass}`}>
        {value}
      </span>
      <span className="label">{label}</span>
      {hint && <span className="text-[11px] text-ink-subtle">{hint}</span>}
    </div>
  );
}
