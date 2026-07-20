"""State tracker update tests (RULES.md 4.10, 8.10, 10)."""

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def _state() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads((REPO_ROOT / "state.json").read_text())
    return payload


def _runs() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = _state()["promptRuns"]
    return runs


def test_state_json_is_valid_and_consistent() -> None:
    state = _state()
    assert state["project"] == "policy-compliance-drift-detection-agent"
    runs = _runs()
    assert runs
    # The tracked current prompt matches the latest recorded run.
    assert state["currentPromptId"] == runs[-1]["promptId"]


def test_every_prompt_run_records_required_fields() -> None:
    for run in _runs():
        for field in (
            "promptId",
            "status",
            "implemented",
            "created",
            "changed",
            "result",
            "drawbacks",
            "validation",
            "nextTriggerPhrase",
        ):
            assert field in run, f"{run.get('promptId')} missing {field}"


def test_implementation_state_md_tracks_current_prompt() -> None:
    state = _state()
    md = (REPO_ROOT / "IMPLEMENTATION_STATE.md").read_text()
    assert f"Current prompt: {state['currentPromptId']}" in md
    # Every recorded prompt run has a section in the markdown tracker.
    for run in _runs():
        assert f"## {run['promptId']}" in md
