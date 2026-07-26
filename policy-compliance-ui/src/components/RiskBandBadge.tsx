import type { RiskBand } from "../types";

const BAND_CLASS: Record<RiskBand, string> = {
  Critical: "border-critical/40 bg-critical/12 text-critical",
  High: "border-high/40 bg-high/12 text-high",
  Medium: "border-medium/40 bg-medium/15 text-medium",
  Low: "border-low/40 bg-low/12 text-low",
};

export function RiskBandBadge({
  band,
  score,
}: {
  band: RiskBand;
  score?: number;
}) {
  return (
    <span className={`chip ${BAND_CLASS[band]}`}>
      {score !== undefined && <span className="font-semibold">{score}</span>}
      {band}
    </span>
  );
}
