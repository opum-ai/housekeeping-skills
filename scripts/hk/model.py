"""Inventory items, levels, safety classes, and the JSON envelope.

An Item is one thing the engine found: a branch, a file, a container. It carries
everything a reviewer needs to decide about it (evidence, class, provenance,
undo) and everything `apply` needs to act on it safely (action, fingerprint).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = 1

LEVELS = ["C1", "C2", "C3", "C4", "C5"]
LEVEL_NAMES = {
    "C1": "Tidy",
    "C2": "Sweep",
    "C3": "Clean",
    "C4": "Deep clean",
    "C5": "Clean room",
}
CLASSES = ["S0", "S1", "S2", "S3"]
PROVENANCE = ("ledger", "attributed", "unknown")

# Exit codes shared with quest and lore so callers branch the same way everywhere.
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_DENIED = 4
EXIT_CONFLICT = 5
EXIT_FINDINGS = 6


def level_index(level: str) -> int:
    lv = level.upper()
    if lv not in LEVELS:
        raise ValueError(f"unknown level {level!r}; expected one of {', '.join(LEVELS)}")
    return LEVELS.index(lv)


def raise_class(cls: str, by: int = 1) -> str:
    """Evidence raises a class; nothing lowers it. Capped at S3."""
    return CLASSES[min(CLASSES.index(cls) + by, len(CLASSES) - 1)]


def max_class(*classes: str) -> str:
    return CLASSES[max(CLASSES.index(c) for c in classes)]


@dataclass
class Item:
    domain: str  # git | files | runtime | harness | caches
    kind: str  # e.g. branch.landed, file.junk, container.stopped
    target: str  # path, ref, container id, pid
    level: str  # the lowest cleanliness level that plans this item
    cls: str  # S0..S3, after evidence adjustments
    op: str  # the action `apply` performs; "report" is never applied
    reason: str  # one line a reviewer can read
    provenance: str = "unknown"
    args: Dict[str, Any] = field(default_factory=dict)
    undo: str = ""
    size: Optional[int] = None
    age_days: Optional[float] = None
    evidence: List[str] = field(default_factory=list)
    fingerprint: Dict[str, Any] = field(default_factory=dict)
    protected: Optional[str] = None  # reason, when the protected set matched
    id: str = ""

    def __post_init__(self) -> None:
        if self.cls not in CLASSES:
            raise ValueError(f"bad class {self.cls}")
        if self.provenance not in PROVENANCE:
            raise ValueError(f"bad provenance {self.provenance}")
        level_index(self.level)
        if not self.id:
            h = hashlib.sha1(f"{self.domain}\0{self.kind}\0{self.target}".encode()).hexdigest()
            self.id = f"{self.domain[:3]}-{h[:8]}"

    @property
    def actionable(self) -> bool:
        return self.op != "report" and self.protected is None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Item":
        return cls(**d)


def envelope(kind: str, data: Any) -> str:
    return json.dumps({"schemaVersion": SCHEMA_VERSION, "kind": kind, "data": data}, indent=2, default=str)


def human_size(n: Optional[int]) -> str:
    if n is None:
        return "-"
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"
