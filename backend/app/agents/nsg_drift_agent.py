"""NSG Drift Management Agent.

Detects broad source CIDR, sensitive management-port exposure, and priority
drift on inbound allow rules, and emits safety-blocker candidates when the
owner or side effects are unknown. Emits signals only — no remediation, no
final score, no route.
"""

from typing import Any

from app.domain.enums import (
    BlockerCode,
    EnvironmentType,
    FocusedSignal,
    ImpactLevel,
)
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.focused_signals import (
    FocusedAgentResult,
    SignalDetection,
    SignalSource,
)

NSG_RESOURCE_TYPE = "microsoft.network/networksecuritygroups"

BROAD_SOURCE_PREFIXES = {"*", "0.0.0.0/0", "internet"}
SENSITIVE_PORTS = {22, 3389, 1433, 5432}
# A port range wider than this is treated as broad exposure by itself.
BROAD_RANGE_WIDTH = 512


def _range_is_sensitive(port_range: str) -> bool:
    """True when the range covers a sensitive management/database port or is
    broad enough to be an exposure by itself. Deterministic and total."""
    value = port_range.strip()
    if value == "*":
        return True
    if "-" in value:
        try:
            low, high = (int(part) for part in value.split("-", 1))
        except ValueError:
            return False
        if high - low >= BROAD_RANGE_WIDTH:
            return True
        return any(low <= port <= high for port in SENSITIVE_PORTS)
    try:
        return int(value) in SENSITIVE_PORTS
    except ValueError:
        return False


class NsgDriftAgent:
    AGENT_NAME = "nsg_drift"

    def applies_to(self, evidence: CanonicalEvidence) -> bool:
        resource_type = evidence.resource_facts.resource_type or ""
        return resource_type.lower() == NSG_RESOURCE_TYPE

    def detect(
        self,
        evidence: CanonicalEvidence,
        runtime_properties: dict[str, Any],
    ) -> FocusedAgentResult:
        result = FocusedAgentResult(
            agent=self.AGENT_NAME, violation_id=evidence.violation_id
        )
        for rule in runtime_properties.get("securityRules") or []:
            self._detect_rule(result, rule)
        self._collect_blocker_candidates(result, evidence)
        return result

    def _detect_rule(self, result: FocusedAgentResult, rule: dict[str, Any]) -> None:
        if rule.get("direction") != "Inbound" or rule.get("access") != "Allow":
            return
        name = rule.get("name", "<unnamed>")

        prefix = str(rule.get("sourceAddressPrefix", ""))
        if prefix.lower() in BROAD_SOURCE_PREFIXES:
            result.signals.append(
                SignalDetection(
                    signal=FocusedSignal.BROAD_SOURCE_CIDR,
                    source=SignalSource.RUNTIME,
                    evidence=f"Rule '{name}' allows sourceAddressPrefix {prefix}",
                )
            )

        port_range = str(rule.get("destinationPortRange", ""))
        if _range_is_sensitive(port_range):
            result.signals.append(
                SignalDetection(
                    signal=FocusedSignal.SENSITIVE_PORT_EXPOSED,
                    source=SignalSource.RUNTIME,
                    evidence=(
                        f"Rule '{name}' allows destination port range {port_range}"
                    ),
                )
            )

        baseline = rule.get("baselinePriority")
        priority = rule.get("priority")
        if baseline is not None and priority is not None and priority != baseline:
            result.signals.append(
                SignalDetection(
                    signal=FocusedSignal.PRIORITY_DRIFT,
                    source=SignalSource.RUNTIME,
                    evidence=(
                        f"Rule '{name}' priority {priority} differs from "
                        f"baseline {baseline}"
                    ),
                )
            )

    def _collect_blocker_candidates(
        self, result: FocusedAgentResult, evidence: CanonicalEvidence
    ) -> None:
        """Safety-blocker candidates only; the routing planner (P10) decides."""
        if evidence.ownership.owner_team is None:
            result.blocker_candidates.append(BlockerCode.MISSING_OWNER)
        if evidence.remediation_eligibility.downtime_risk is ImpactLevel.UNKNOWN:
            result.blocker_candidates.append(BlockerCode.UNKNOWN_DOWNTIME_RISK)
        if evidence.risk_signals.dependency_count is None:
            result.blocker_candidates.append(BlockerCode.UNKNOWN_DEPENDENCY_IMPACT)
        if evidence.resource_facts.environment is EnvironmentType.PRODUCTION:
            result.blocker_candidates.append(BlockerCode.PRODUCTION_RUNTIME_CHANGE)
