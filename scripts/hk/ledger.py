"""The provenance ledger: what agent sessions recorded creating.

One JSONL file per session under `<repo>/.claude/housekeeping/ledger/`. The
capture hook appends to it; `hk ledger add` lets a skill record by hand. The
directory is gitignored: provenance is machine-local evidence, not history.
"""
from __future__ import annotations

import json
import os
import time
from typing import Dict, Optional

KINDS = ("file", "dir", "branch", "worktree", "container", "process")


def ledger_dir(root: str) -> str:
    return os.path.join(root, ".claude", "housekeeping", "ledger")


def add(root: str, kind: str, target: str, session: Optional[str] = None, cmd: Optional[str] = None,
        cwd: Optional[str] = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"unknown ledger kind {kind!r}; expected one of {', '.join(KINDS)}")
    session = session or os.environ.get("CLAUDE_CODE_SESSION_ID") or "unknown-session"
    d = ledger_dir(root)
    os.makedirs(d, exist_ok=True)
    if kind in ("file", "dir", "worktree") and not os.path.isabs(target):
        target = os.path.abspath(os.path.join(cwd or root, target))
    entry = {"ts": time.time(), "session": session, "kind": kind, "target": target}
    if cmd:
        entry["cmd"] = cmd
    with open(os.path.join(d, f"{session}.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def load(root: str, session: Optional[str] = None) -> Dict[str, Dict[str, dict]]:
    """kind -> {target: entry}. For processes the key is the recorded command."""
    out: Dict[str, Dict[str, dict]] = {k: {} for k in KINDS}
    d = ledger_dir(root)
    if not os.path.isdir(d):
        return out
    for name in sorted(os.listdir(d)):
        if not name.endswith(".jsonl"):
            continue
        if session and name != f"{session}.jsonl":
            continue
        with open(os.path.join(d, name), encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = e.get("kind")
                if kind not in out:
                    continue
                key = e.get("cmd") if kind == "process" else e.get("target")
                if key:
                    out[kind][key] = e
    return out
