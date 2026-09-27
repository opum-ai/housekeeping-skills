"""`.housekeeping.toml` loading with built-in defaults.

Python 3.11+ parses with tomllib; 3.9/3.10 fall back to `mini_toml`, which
covers the subset this file uses: tables, strings, numbers, booleans, and flat
arrays of scalars.
"""
from __future__ import annotations

import ast
import copy
import os
import re
from typing import Any, Dict

CONFIG_NAME = ".housekeeping.toml"

DEFAULTS: Dict[str, Any] = {
    "version": 1,
    "housekeeping_level": "standard",  # minimal | light | standard | deep | immaculate
    "housekeeping_scope": "repo",  # session | repo | machine
    # Context -> level, for when the user names no level.
    "levels": {"checkpoint": "minimal", "session_end": "light", "default": "standard", "task_done": "standard"},
    "sdlc": {"trunk": "", "release": "", "merge": "squash", "remote": "origin"},
    "protect": {
        "branches": ["retain/*", "preserve/*", "archive/*"],
        "paths": [],
        "containers": ["opum-runner"],
        "images": ["*opum-actions-runner*"],
    },
    "junk": {"patterns": []},
    "tmp": {"prefixes": [], "max_age_days": 2},
    "stash": {"max_age_days": 30},
    "branches": {"stale_days": 30},
    "scratchpad": {"max_age_days": 3},
    "provenance": {"enabled": False},
    # Immaculate: files that are deliberately kept (they get the disposition "kept: keep-list"),
    # and the commands that verify the final state (e.g. a from-scratch build and test).
    "immaculate": {"keep": [".env", ".env.local"], "verify": []},
    "docker": {"projects": []},
}


def mini_toml(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    cur = out
    pending_key = None
    pending_val = ""
    for raw in text.splitlines():
        line = _strip_comment(raw).strip()
        if pending_key is not None:
            pending_val += " " + line
            if _balanced(pending_val):
                cur[pending_key] = _value(pending_val)
                pending_key = None
            continue
        if not line:
            continue
        m = re.fullmatch(r"\[([A-Za-z0-9_.\-]+)\]", line)
        if m:
            cur = out
            for part in m.group(1).split("."):
                cur = cur.setdefault(part, {})
            continue
        if "=" not in line:
            raise ValueError(f"cannot parse config line: {raw!r}")
        key, val = (s.strip() for s in line.split("=", 1))
        key = key.strip('"')
        if not _balanced(val):
            pending_key, pending_val = key, val
            continue
        cur[key] = _value(val)
    return out


def _strip_comment(line: str) -> str:
    in_str = None
    for i, ch in enumerate(line):
        if in_str:
            if ch == in_str and line[i - 1] != "\\":
                in_str = None
        elif ch in "\"'":
            in_str = ch
        elif ch == "#":
            return line[:i]
    return line


def _balanced(val: str) -> bool:
    return val.count("[") == val.count("]")


def _value(val: str) -> Any:
    val = val.strip()
    if val in ("true", "false"):
        return val == "true"
    if val.startswith("["):
        inner = val[1:-1].strip().rstrip(",")
        if not inner:
            return []
        py = inner.replace("true", "True").replace("false", "False")
        return list(ast.literal_eval("[" + py + "]"))
    if val.startswith(("'", '"')):
        return ast.literal_eval(val)
    try:
        return int(val)
    except ValueError:
        return float(val)


def _merge(base: Dict[str, Any], over: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        elif k in ("branches", "paths", "containers", "images", "patterns", "prefixes", "keep") and isinstance(
            base.get(k), list
        ):
            # Protected and pattern lists extend the built-ins; they never replace them.
            base[k] = list(dict.fromkeys(base[k] + list(v)))
        else:
            base[k] = v
    return base


def load(root: str) -> Dict[str, Any]:
    cfg = copy.deepcopy(DEFAULTS)
    path = os.path.join(root, CONFIG_NAME)
    if not os.path.exists(path):
        return cfg
    with open(path, "rb") as fh:
        raw = fh.read().decode()
    try:
        import tomllib  # type: ignore[import-not-found]

        parsed = tomllib.loads(raw)
    except ImportError:
        parsed = mini_toml(raw)
    return _merge(cfg, parsed)
