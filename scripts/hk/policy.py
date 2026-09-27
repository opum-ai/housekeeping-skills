"""Honour the user's Claude Code permission rules inside `hk apply`.

`hk apply` performs deletions on the user's behalf. It must never become a way
around a rule the user set for the harness (for example an auto-mode soft deny
on `git branch -D`). Every planned action is expressed as the shell command it
is equivalent to, and matched against the Bash rules in the user, project, and
local settings:
- `permissions.deny`                     -> refused
- `permissions.ask`, `autoMode.soft_deny` -> needs a per-item --confirm naming the rule
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
from typing import Dict, List, Optional, Tuple

from .model import Item

RULE = re.compile(r"^\s*Bash\((.*?)\)")


def _settings_files(root: str) -> List[str]:
    from .harness import claude_home

    return [os.path.join(claude_home(), "settings.json"), os.path.join(claude_home(), "settings.local.json"),
            os.path.join(root, ".claude", "settings.json"), os.path.join(root, ".claude", "settings.local.json")]


def load_rules(root: str) -> Dict[str, List[Tuple[str, str]]]:
    """{"deny": [(pattern, source)], "ask": [...]} from every settings layer."""
    out: Dict[str, List[Tuple[str, str]]] = {"deny": [], "ask": []}
    for f in _settings_files(root):
        try:
            data = json.load(open(f))
        except (OSError, json.JSONDecodeError):
            continue
        perms = data.get("permissions") or {}
        auto = data.get("autoMode") or {}
        for key, bucket in (("deny", perms.get("deny")), ("ask", perms.get("ask")), ("ask", auto.get("soft_deny"))):
            for entry in bucket or []:
                m = RULE.match(str(entry))
                if m:
                    out[key].append((m.group(1).strip(), f"{os.path.basename(f)}: {str(entry)[:120]}"))
    return out


def _matches(pattern: str, command: str) -> bool:
    if pattern.endswith(":*"):
        return command == pattern[:-2] or command.startswith(pattern[:-2] + " ")
    if "*" in pattern:
        return fnmatch.fnmatchcase(command, pattern)
    return command == pattern


def equivalent_command(it: Item) -> str:
    a, op, q = it.args, it.op, shlex.quote
    if op in ("git-branch-delete", "git-archive-branch"):
        return f"git branch -D {q(a['name'])}"
    if op == "git-push-delete":
        return f"git push {q(a['remote'])} --delete {q(a['name'])}"
    if op == "git-worktree-remove":
        return f"git worktree remove {q(a['path'])}"
    if op == "git-worktree-prune":
        return "git worktree prune"
    if op == "git-stash-archive-drop":
        return f"git stash drop {a.get('sha', '')[:12]}"
    if op == "trash":
        return f"trash {q(it.target)}"
    if op == "rm":
        return f"rm -rf {q(it.target)}"
    if op == "rm-children":
        return f"rm -rf {q(a['path'])}/*"
    if op == "rm-files":
        return "rm " + " ".join(q(f) for f in a.get("files", [])[:3]) + (" ..." if len(a.get("files", [])) > 3 else "")
    if op == "kill":
        return f"kill {a['pid']}"
    docker = {"docker-stop": "stop", "docker-rm": "rm", "docker-rmi": "rmi"}
    if op in docker:
        return f"docker {docker[op]} {a['id'][:12]}"
    if op == "docker-volume-rm":
        return f"docker volume rm {q(a['name'])}"
    if op == "docker-network-rm":
        return f"docker network rm {q(a['name'])}"
    if op == "cmd":
        return " ".join(q(x) for x in a.get("argv", []))
    return op


def verdict(it: Item, rules: Dict[str, List[Tuple[str, str]]]) -> Tuple[Optional[str], Optional[str]]:
    """("deny" | "ask" | None, the rule that matched)."""
    cmd = equivalent_command(it)
    for kind in ("deny", "ask"):
        for pattern, source in rules[kind]:
            if _matches(pattern, cmd):
                return kind, source
    return None, None
