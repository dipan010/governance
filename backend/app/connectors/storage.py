"""Evidence packet store (Azure Storage Account stand-in).

The Protocol is the seam for swapping the local JSON store for Azure Blob
Storage with managed identity later. Content is masked before writing.
"""

import json
from pathlib import Path
from typing import Any, Protocol

from app.core.logging import mask_sensitive


class EvidencePacketStore(Protocol):
    def put(self, violation_id: str, name: str, content: dict[str, Any]) -> str: ...


class LocalEvidencePacketStore:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def put(self, violation_id: str, name: str, content: dict[str, Any]) -> str:
        target_dir = self._base_dir / violation_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{name}.json"
        target.write_text(json.dumps(mask_sensitive(content), indent=2, default=str))
        return f"local://evidence_packets/{violation_id}/{name}.json"
