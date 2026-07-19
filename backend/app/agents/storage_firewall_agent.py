"""Storage Firewall Compliance Agent.

Detects storage account public exposure and network-rule drift from runtime
properties, inventory facts, and the IaC source mapping. Emits signals only.
"""

from typing import Any

from app.connectors.repo_map import RepoMapping
from app.domain.enums import DataClassification, FocusedSignal
from app.domain.evidence_schema import CanonicalEvidence
from app.domain.focused_signals import (
    FocusedAgentResult,
    SignalDetection,
    SignalSource,
)

STORAGE_RESOURCE_TYPE = "microsoft.storage/storageaccounts"

# Source properties that re-enable public exposure when drifted.
PUBLIC_ACCESS_SOURCE_PROPERTIES = (
    "public_network_access_enabled",
    "network_rules.default_action",
)


class StorageFirewallAgent:
    AGENT_NAME = "storage_firewall"

    def applies_to(self, evidence: CanonicalEvidence) -> bool:
        resource_type = evidence.resource_facts.resource_type or ""
        return resource_type.lower() == STORAGE_RESOURCE_TYPE

    def detect(
        self,
        evidence: CanonicalEvidence,
        runtime_properties: dict[str, Any],
        repo_mapping: RepoMapping | None,
    ) -> FocusedAgentResult:
        result = FocusedAgentResult(
            agent=self.AGENT_NAME, violation_id=evidence.violation_id
        )
        self._detect_public_network_access(result, runtime_properties)
        self._detect_firewall_default_allow(result, runtime_properties)
        self._detect_private_endpoint_gap(result, evidence, runtime_properties)
        self._detect_source_drift(result, repo_mapping)
        return result

    def _detect_public_network_access(
        self, result: FocusedAgentResult, properties: dict[str, Any]
    ) -> None:
        if properties.get("publicNetworkAccess") == "Enabled":
            result.signals.append(
                SignalDetection(
                    signal=FocusedSignal.STORAGE_PUBLIC_NETWORK_ACCESS,
                    source=SignalSource.RUNTIME,
                    evidence="publicNetworkAccess is Enabled",
                )
            )

    def _detect_firewall_default_allow(
        self, result: FocusedAgentResult, properties: dict[str, Any]
    ) -> None:
        network_acls = properties.get("networkAcls") or {}
        if network_acls.get("defaultAction") == "Allow":
            result.signals.append(
                SignalDetection(
                    signal=FocusedSignal.STORAGE_FIREWALL_DEFAULT_ALLOW,
                    source=SignalSource.RUNTIME,
                    evidence="networkAcls.defaultAction is Allow",
                )
            )

    def _detect_private_endpoint_gap(
        self,
        result: FocusedAgentResult,
        evidence: CanonicalEvidence,
        properties: dict[str, Any],
    ) -> None:
        restricted = (
            evidence.risk_signals.data_classification is DataClassification.RESTRICTED
        )
        has_private_endpoint = bool(properties.get("privateEndpointConnections"))
        if restricted and not has_private_endpoint:
            result.signals.append(
                SignalDetection(
                    signal=FocusedSignal.PRIVATE_ENDPOINT_GAP,
                    source=SignalSource.INVENTORY,
                    evidence=(
                        "Data classification is Restricted and no private "
                        "endpoint connection exists"
                    ),
                )
            )

    def _detect_source_drift(
        self, result: FocusedAgentResult, repo_mapping: RepoMapping | None
    ) -> None:
        if repo_mapping is None:
            return
        drifted = repo_mapping.drifted_properties()
        for name in PUBLIC_ACCESS_SOURCE_PROPERTIES:
            prop = drifted.get(name)
            if prop is not None:
                result.signals.append(
                    SignalDetection(
                        signal=FocusedSignal.SOURCE_DRIFT_LIKELY,
                        source=SignalSource.SOURCE,
                        evidence=(
                            f"{repo_mapping.repo_path}: {name} is "
                            f"'{prop.current_source_value}', expected "
                            f"'{prop.expected_source_value}'"
                        ),
                    )
                )
                return  # one source-drift signal is enough
