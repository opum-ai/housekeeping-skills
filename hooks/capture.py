#!/usr/bin/env python3
"""Provenance capture hook (opt-in, fail-open).

Records what an agent session creates, so housekeeping can later remove exactly
those things (spec R-3, ADR-0004):
- PreToolUse Write/Edit/NotebookEdit on a path that does not exist yet -> file
- PostToolUse Bash:
  - `git worktree add` -> worktree (and its -b branch)
  - `git checkout -b` / `git switch -c` / `git branch <name>` -> branch
  - `docker run --name` -> container
  - `mktemp` output -> file/dir
  - run_in_background -> process

A no-op unless the repository's .housekeeping.toml sets `[provenance] enabled = true`.
A hook must never break the session it is attached to: every failure path exits 0
and prints nothing.
"""
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))


def repo_root(cwd):
    d = os.path.abspath(cwd or ".")
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def enabled(root):
    path = os.path.join(root, ".housekeeping.toml")
    if not os.path.exists(path):
        return False
    from hk import config

    return bool(config.load(root).get("provenance", {}).get("enabled"))


def _abs(cwd, p):
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(cwd, p))


def from_bash(cmd, cwd, response, background):
    out = []
    for segment in re.split(r"&&|\|\||;|\n", cmd):
        try:
            toks = shlex.split(segment)
        except ValueError:
            continue
        if not toks:
            continue
        if toks[0] == "git":
            toks = [t for i, t in enumerate(toks) if not (i > 0 and toks[i - 1] == "-C")][1:]
            toks = [t for t in toks if t != "-C"]
            if toks[:2] == ["worktree", "add"]:
                args = toks[2:]
                if "-b" in args or "-B" in args:
                    flag = "-b" if "-b" in args else "-B"
                    i = args.index(flag)
                    if i + 1 < len(args):
                        out.append(("branch", args[i + 1], None))
                    args = args[:i] + args[i + 2:]
                pos = [a for a in args if not a.startswith("-")]
                if pos:
                    out.append(("worktree", _abs(cwd, pos[0]), None))
            elif toks[:1] == ["checkout"] and len(toks) >= 3 and toks[1] in ("-b", "-B"):
                out.append(("branch", toks[2], None))
            elif toks[:1] == ["switch"] and len(toks) >= 3 and toks[1] in ("-c", "-C", "--create"):
                out.append(("branch", toks[2], None))
            elif toks[:1] == ["branch"] and len(toks) >= 2 and not toks[1].startswith("-"):
                out.append(("branch", toks[1], None))
        elif toks[:2] == ["docker", "run"] and "--name" in toks:
            i = toks.index("--name")
            if i + 1 < len(toks):
                out.append(("container", toks[i + 1], None))
        elif toks[0] == "mktemp" and response:
            for line in str(response).splitlines():
                line = line.strip()
                if line.startswith("/") and os.path.exists(line):
                    out.append(("dir" if os.path.isdir(line) else "file", line, None))
    if background:
        out.append(("process", cmd.strip()[:300], cmd.strip()[:300]))
    return out


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        cwd = payload.get("cwd") or os.getcwd()
        root = repo_root(cwd)
        if not root or not enabled(root):
            return 0
        from hk import ledger

        session = payload.get("session_id")
        tool = payload.get("tool_name", "")
        event = payload.get("hook_event_name", "")
        ti = payload.get("tool_input") or {}
        records = []
        if event == "PreToolUse" and tool in ("Write", "Edit", "NotebookEdit"):
            p = ti.get("file_path") or ti.get("notebook_path")
            if p and not os.path.exists(_abs(cwd, p)):
                records.append(("file", _abs(cwd, p), None))
        elif event == "PostToolUse" and tool == "Bash":
            resp = payload.get("tool_response")
            if isinstance(resp, dict):
                resp = resp.get("stdout", "")
            records = from_bash(ti.get("command", ""), cwd, resp, bool(ti.get("run_in_background")))
        for kind, target, cmd in records:
            ledger.add(root, kind, target, session=session, cmd=cmd, cwd=cwd)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
