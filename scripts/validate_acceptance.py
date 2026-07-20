"""Acceptance validation: proves every MVP acceptance criterion (AC-1..AC-9)
against the running application, end to end, using the fixture data.

Usage (from repo root):
    backend/.venv/bin/python scripts/validate_acceptance.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

# Isolated throwaway database; local mode creates the schema on startup.
_tmpdir = tempfile.mkdtemp(prefix="acceptance-")
os.environ["PCDA_DATABASE_URL"] = f"sqlite+pysqlite:///{_tmpdir}/acceptance.db"
os.environ["PCDA_ENVIRONMENT"] = "local"
os.environ["PCDA_EVIDENCE_PACKETS_DIR"] = f"{_tmpdir}/evidence_packets"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

RESULTS: list[tuple[str, str, bool, str]] = []


def check(criterion: str, name: str, passed: bool, proof: str) -> None:
    RESULTS.append((criterion, name, passed, proof))


def main() -> int:
    fixture = json.loads(
        (REPO_ROOT / "data" / "fixtures" / "policy_findings.json").read_text()
    )

    with TestClient(app) as client:
        # AC-1: at least five non-compliance records processed
        ingest = client.post("/api/ingest/policy", json=fixture).json()
        check(
            "AC-1",
            "five findings ingested and normalized",
            ingest["ingested"] >= 5 and ingest["errors"] == 0,
            f"ingested={ingest['ingested']} errors={ingest['errors']}",
        )

        # AC-2: core agent plus at least two focused agents
        pol001 = client.get("/api/violations/POL-001").json()
        pol002 = client.get("/api/violations/POL-002").json()
        storage_signals = set(
            pol001["evidence"]["riskSignals"]["focusedSignals"]
        )
        nsg_signals = set(pol002["evidence"]["riskSignals"]["focusedSignals"])
        check(
            "AC-2",
            "storage and NSG focused agents emit signals",
            "storage_public_network_access" in storage_signals
            and "broad_source_cidr" in nsg_signals,
            f"storage={sorted(storage_signals)} nsg={sorted(nsg_signals)}",
        )

        # AC-3: every record has score, owner or owner gap, route,
        # verification query
        worklist = client.get("/api/violations?sort=ranked").json()
        ac3 = True
        for summary in worklist:
            detail = client.get(f"/api/violations/{summary['violationId']}").json()
            evidence = detail["evidence"]
            has_owner_or_gap = (
                evidence["ownership"]["ownerTeam"] is not None
                or "missing_owner" in detail["missingEvidence"]
            )
            if not (
                evidence["decision"]["riskScore"] is not None
                and has_owner_or_gap
                and evidence["decision"]["recommendedPath"]
                and evidence["verification"]["verificationQuery"]
            ):
                ac3 = False
        check(
            "AC-3",
            "each record has score, owner/gap, route, verification query",
            ac3,
            f"checked {len(worklist)} violations",
        )

        # AC-4: ranking differs from raw severity sorting
        raw_ids = [
            v["violationId"] for v in client.get("/api/violations?sort=raw").json()
        ]
        ranked_ids = [v["violationId"] for v in worklist]
        check(
            "AC-4",
            "agent ranking differs from raw severity order",
            raw_ids != ranked_ids and raw_ids[0] == "POL-002"
            and ranked_ids[0] == "POL-001",
            f"raw={raw_ids} ranked={ranked_ids}",
        )

        # AC-5: one ticket/change route
        pol002_artifacts = client.post("/api/violations/POL-002/artifact").json()
        check(
            "AC-5",
            "ticket generated",
            any(a["kind"] == "ticket" for a in pol002_artifacts),
            f"kinds={[a['kind'] for a in pol002_artifacts]}",
        )

        # AC-6: one source PR/comment route
        pol001_artifacts = client.post("/api/violations/POL-001/artifact").json()
        pr = next(
            (a for a in pol001_artifacts if a["kind"] == "pr_comment_preview"), None
        )
        check(
            "AC-6",
            "PR/comment preview generated with source fix",
            pr is not None and "storage_account.tf" in pr["body"],
            f"kinds={[a['kind'] for a in pol001_artifacts]}",
        )

        # AC-7: one remediation dry-run after approval
        denied = client.post("/api/violations/POL-003/artifact")
        client.post("/api/violations/POL-003/approval-request")
        client.post(
            "/api/violations/POL-003/approve",
            json={"decision": "approve", "approver": "cloudgov-approver"},
        )
        approved = client.post("/api/violations/POL-003/artifact")
        check(
            "AC-7",
            "dry-run blocked without approval, generated after approval",
            denied.status_code == 403
            and approved.status_code == 200
            and approved.json()[0]["kind"] == "remediation_dry_run",
            f"before={denied.status_code} after={approved.status_code}",
        )

        # AC-8: one blocked/exception unsafe action
        blocked_card = client.post("/api/violations/POL-005/artifact").json()
        check(
            "AC-8",
            "blocked card with rule reason for ownerless finding",
            blocked_card[0]["kind"] == "blocked_card"
            and "missing owner blocks auto-action" in blocked_card[0]["body"],
            f"kind={blocked_card[0]['kind']}",
        )

        # AC-9: before/after verification with audit packet
        premature = client.post("/api/violations/POL-001/close")
        verify = client.post("/api/violations/POL-001/verify").json()
        closed = client.post("/api/violations/POL-001/close")
        audit = client.get("/api/audit/POL-001").json()
        packet = next(
            (
                e["evidencePacket"]
                for e in audit
                if e["eventType"] == "verification.completed"
            ),
            None,
        )
        check(
            "AC-9",
            "before/after verification, proof-gated closure, audit packet",
            premature.status_code == 409
            and verify["result"] == "Compliant"
            and verify["beforeState"]["publicNetworkAccess"] == "Enabled"
            and verify["afterState"]["publicNetworkAccess"] == "Disabled"
            and closed.status_code == 200
            and packet is not None,
            f"verify={verify['result']} packet={packet}",
        )

    width = max(len(name) for _, name, _, _ in RESULTS)
    print("\nAcceptance criteria results")
    print("=" * (width + 20))
    failed = 0
    for criterion, name, passed, proof in RESULTS:
        status = "PASS" if passed else "FAIL"
        if not passed:
            failed += 1
        print(f"{criterion}  {status}  {name.ljust(width)}  [{proof}]")
    print("=" * (width + 20))
    print(f"{len(RESULTS) - failed}/{len(RESULTS)} criteria passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
