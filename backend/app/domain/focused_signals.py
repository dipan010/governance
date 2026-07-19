"""Shared model for focused-agent signal emission.

Focused agents (Storage Firewall, NSG Drift) emit domain signals with the
evidence fact that backs each one. They never set the final score or route —
the central scorer (P08) and routing planner (P10) own those decisions.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.domain.enums import BlockerCode, FocusedSignal
from app.domain.evidence_schema import CanonicalEvidence


class SignalSource(StrEnum):
    RUNTIME = "runtime"
    SOURCE = "source"
    INVENTORY = "inventory"


class SignalDetection(BaseModel):
    signal: FocusedSignal
    source: SignalSource
    evidence: str


class FocusedAgentResult(BaseModel):
    agent: str
    violation_id: str
    signals: list[SignalDetection] = Field(default_factory=list)
    blocker_candidates: list[BlockerCode] = Field(default_factory=list)


def merge_signals(evidence: CanonicalEvidence, result: FocusedAgentResult) -> None:
    """Attach detected signals to the finding card data, without duplicates."""
    existing = set(evidence.risk_signals.focused_signals)
    for detection in result.signals:
        if detection.signal not in existing:
            evidence.risk_signals.focused_signals.append(detection.signal)
            existing.add(detection.signal)
