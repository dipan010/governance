import type { Decision } from "../api/types";

export function ScoreBreakdown({ decision }: { decision: Decision }) {
  return (
    <section aria-label="Risk explanation" className="panel">
      <h3>Risk explanation</h3>
      <p>
        Risk score <strong>{decision.riskScore ?? "–"}</strong> (
        {decision.riskBand ?? "unscored"}) · Actionability{" "}
        <strong>{decision.actionabilityScore ?? "–"}</strong>
      </p>
      <h4>Score factors</h4>
      <ul>
        {decision.scoreFactors.map((factor) => (
          <li key={factor}>{factor}</li>
        ))}
      </ul>
      <h4>Actionability factors</h4>
      <ul>
        {decision.actionabilityFactors.map((factor) => (
          <li key={factor}>{factor}</li>
        ))}
      </ul>
      <h4>Blockers</h4>
      {decision.blockers.length ? (
        <ul className="blockers" aria-label="Blockers">
          {decision.blockers.map((blocker) => (
            <li key={blocker} className="blocker">
              {blocker}
            </li>
          ))}
        </ul>
      ) : (
        <p>none</p>
      )}
      <p className="rule-version">
        score rules: {decision.scoreRuleVersion ?? "–"} · route rules:{" "}
        {decision.routeRuleVersion ?? "–"}
      </p>
    </section>
  );
}
