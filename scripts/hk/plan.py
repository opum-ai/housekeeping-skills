"""Plan, apply, journal, undo.

`apply` executes exactly the reviewed plan (spec R-6):
- each item's fingerprint is re-checked and a changed target is skipped;
- S2 items need the batch approval flag, S3 items need their id confirmed;
- every action is appended to a journal with its undo recipe.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import tempfile
import time
from typing import Dict, List, Optional, Sequence, Tuple

from .files import scratchpad_root
from .git import Repo
from .harness import claude_home
from .model import CLASSES, Item, level_index, normalize_level, scope_index
from .policy import equivalent_command, load_rules, verdict
from .util import (file_fingerprint, state_dir, fallback_trash_dir, protected_path, run, trash_command, within)


def hk_dir(root: str, sub: str) -> str:
    return state_dir(root, sub)


def build_plan(items: List[Item], level: str, root: str, notes: List[str], chosen_by: str = "",
               scope: str = "repo") -> dict:
    li, si = level_index(level), scope_index(scope)
    planned, findings = [], []
    for it in items:
        if level_index(it.level) > li or scope_index(it.scope) > si:
            continue
        (planned if it.actionable else findings).append(it)
    planned.sort(key=lambda i: (CLASSES.index(i.cls), i.domain, i.kind, i.target))
    # A target that is planned for action needs no separate "finding" line.
    planned_targets = {i.target for i in planned}
    findings = [f for f in findings if f.target not in planned_targets]
    rules = load_rules(root)
    by_class: Dict[str, dict] = {}
    for it in planned:
        b = by_class.setdefault(it.cls, {"count": 0, "bytes": 0})
        b["count"] += 1
        b["bytes"] += it.size or 0
    return {
        "level": normalize_level(level),
        "scope": scope,
        "chosen_by": chosen_by,
        "root": root,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "summary": {"by_class": by_class, "planned": len(planned), "findings": len(findings)},
        "items": [_annotate(i, rules) for i in planned],
        "findings": [i.to_dict() for i in findings],
        "notes": notes,
    }


def _annotate(it: Item, rules) -> dict:
    d = it.to_dict()
    d["command"] = equivalent_command(it)
    v, rule = verdict(it, rules)
    if v:
        d["policy"] = {"verdict": v, "rule": rule}
    return d


def save_plan(plan: dict, root: str, out: Optional[str] = None) -> str:
    path = out or os.path.join(hk_dir(root, "plans"), f"{time.strftime('%Y%m%dT%H%M%S')}-{plan['level']}.json")
    with open(path, "w") as fh:
        json.dump({"schemaVersion": 1, "kind": "hk.plan", "data": plan}, fh, indent=2, default=str)
    return path


def load_plan(path: str) -> dict:
    with open(path) as fh:
        doc = json.load(fh)
    return doc.get("data", doc)


# ---------------------------------------------------------------------------
# Safety re-checks


def _allowed_roots(root: str, kind: str) -> List[str]:
    """Where an item of this kind may live. Scoped per kind: a repo file item may
    never reach into $TMPDIR, and a temp item may never reach into the repo."""
    if kind.startswith("tmp."):
        return [tempfile.gettempdir()]
    if kind.startswith("scratchpad."):
        return [scratchpad_root()]
    if kind.startswith("project."):
        return [os.path.join(claude_home(), "projects")]
    if kind.startswith("plugin."):
        return [os.path.join(claude_home(), "plugins")]
    if kind == "cache.xcode":
        return [os.path.expanduser("~/Library/Developer/Xcode/DerivedData")]
    return [root]


def _path_ok(root: str, path: str, kind: str, cfg_protect: Sequence[str]) -> Tuple[bool, str]:
    if not within(path, _allowed_roots(root, kind)):
        return False, "outside the allowed roots"
    rroot = os.path.realpath(root)
    rp = os.path.join(os.path.realpath(os.path.dirname(os.path.abspath(path))), os.path.basename(path))
    if rp.startswith(rroot + os.sep):
        rel = os.path.relpath(rp, rroot)
        hit = protected_path(rel, cfg_protect)
        if hit:
            return False, f"protected path ({hit})"
        tracked = run(["git", "-C", root, "ls-files", "--error-unmatch", "--", rel])[0] == 0
        if tracked:
            return False, "tracked by git"
    return True, ""


def recheck(item: Item, repo: Repo) -> Tuple[bool, str]:
    fp = item.fingerprint
    op = item.op
    if op in ("trash", "rm"):
        now = file_fingerprint(item.target)
        if not now.get("exists"):
            return False, "already gone"
        for k in ("mtime_ns", "size", "ino"):
            if k in fp and fp[k] != now.get(k):
                return False, f"changed since planning ({k})"
        return True, ""
    if op in ("git-branch-delete", "git-archive-branch"):
        name = item.args["name"]
        tip = repo.out("rev-parse", "--verify", "--quiet", f"refs/heads/{name}")
        if tip != fp.get("tip"):
            return False, "branch moved since planning" if tip else "branch already gone"
        if name == repo.current_branch() or any(w.get("branch") == name for w in repo.worktrees()):
            return False, "branch is checked out"
        return True, ""
    if op == "git-push-delete":
        tip = repo.out("rev-parse", "--verify", "--quiet", f"refs/remotes/{item.args['remote']}/{item.args['name']}")
        return (tip == fp.get("tip"), "" if tip == fp.get("tip") else "remote branch moved since planning")
    if op == "git-worktree-remove":
        if not os.path.isdir(item.target):
            return False, "worktree already gone"
        dirty = repo.dirty_count(item.target)
        if dirty:
            return False, f"worktree now has {dirty} uncommitted change(s)"
        return True, ""
    if op == "git-stash-archive-drop":
        shas = repo.out("stash", "list", "--format=%H").split()
        return (fp.get("sha") in shas, "" if fp.get("sha") in shas else "stash already gone")
    if op == "kill":
        pid = int(item.args["pid"])
        code, out, _ = run(["ps", "-o", "etime=,command=", "-p", str(pid)])
        if code != 0 or not out.strip():
            return False, "process already exited"
        from .util import parse_etime

        et, _, cmd = out.strip().partition(" ")
        started = time.time() - (parse_etime(et) or 0)
        if abs(started - float(fp.get("started", 0))) > 10 or not cmd.strip().startswith(fp.get("cmd", "")[:40]):
            return False, "pid now belongs to a different process"
        return True, ""
    if op in ("docker-stop", "docker-rm"):
        code, out, _ = run(["docker", "inspect", "--format", "{{.State.Status}}", item.args["id"]])
        if code != 0:
            return False, "container already gone"
        return True, ""
    return True, ""


# ---------------------------------------------------------------------------
# Execution


def _trash(path: str) -> Tuple[bool, str, Optional[List[str]]]:
    cmd = trash_command()
    if cmd:
        code, _, err = run(cmd + [path], timeout=300)
        return code == 0, err.strip(), None
    dest_dir = fallback_trash_dir()
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(path))
    shutil.move(path, dest)
    return True, f"moved to {dest}", ["mv", dest, path]


def _rm(path: str) -> None:
    if os.path.islink(path) or not os.path.isdir(path):
        os.unlink(path)
    else:
        shutil.rmtree(path)


def execute(item: Item, repo: Repo, force_kill: bool = False) -> Tuple[bool, str, Optional[List[str]]]:
    op, a = item.op, item.args
    g = repo.git
    if op == "trash":
        return _trash(item.target)
    if op == "rm":
        _rm(item.target)
        return True, "", None
    if op == "rm-children":
        for name in os.listdir(a["path"]):
            _rm(os.path.join(a["path"], name))
        return True, "", None
    if op == "rm-files":
        removed = 0
        for f in a["files"]:
            if a.get("pid_markers"):
                from .harness import _pid_alive

                if _pid_alive(int(os.path.basename(f))):
                    continue
            try:
                os.unlink(f)
                removed += 1
            except OSError:
                pass
        return True, f"removed {removed}", None
    if op == "git-branch-delete":
        tip = item.fingerprint["tip"]
        code, _, err = g("branch", "-D", a["name"])
        return code == 0, err.strip(), ["git", "-C", repo.root, "branch", a["name"], tip]
    if op == "git-archive-branch":
        tip = item.fingerprint["tip"]
        code, _, err = g("update-ref", a["archive_ref"], tip)
        if code != 0:
            return False, f"could not write archive ref: {err.strip()}", None
        code, _, err = g("branch", "-D", a["name"])
        return code == 0, f"archived at {a['archive_ref']}" if code == 0 else err.strip(), [
            "git", "-C", repo.root, "branch", a["name"], tip]
    if op == "git-push-delete":
        tip = item.fingerprint["tip"]
        code, _, err = g("push", f"--force-with-lease=refs/heads/{a['name']}:{tip}", a["remote"],
                         f":refs/heads/{a['name']}", timeout=120)
        return code == 0, err.strip()[-300:], ["git", "-C", repo.root, "push", a["remote"], f"{tip}:refs/heads/{a['name']}"]
    if op == "git-worktree-remove":
        code, _, err = g("worktree", "remove", a["path"])  # never --force: a dirty tree must refuse
        branch = a.get("branch")
        undo = ["git", "-C", repo.root, "worktree", "add", a["path"], branch] if branch else None
        return code == 0, err.strip(), undo
    if op == "git-worktree-prune":
        code, _, err = g("worktree", "prune", "-v")
        return code == 0, err.strip(), None
    if op == "git-stash-archive-drop":
        sha = a["sha"]
        code, _, err = g("update-ref", f"refs/archive/stash/{sha}", sha)
        if code != 0:
            return False, err.strip(), None
        shas = repo.out("stash", "list", "--format=%H").split()
        idx = shas.index(sha)
        code, _, err = g("stash", "drop", f"stash@{{{idx}}}")
        return code == 0, f"kept at refs/archive/stash/{sha}", ["git", "-C", repo.root, "stash", "store", "-m", a.get("message", ""), sha]
    if op == "kill":
        pid = int(a["pid"])
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True, "terminated (SIGTERM)", None
        if force_kill:
            os.kill(pid, signal.SIGKILL)
            return True, "killed (SIGKILL after SIGTERM timeout)", None
        return False, "still running 5s after SIGTERM; not escalated (use --force-kill)", None
    if op == "docker-stop":
        code, _, err = run(["docker", "stop", a["id"]], timeout=120)
        return code == 0, err.strip(), ["docker", "start", a["id"]]
    if op == "docker-rm":
        code, _, err = run(["docker", "rm", a["id"]], timeout=120)
        return code == 0, err.strip(), None
    if op == "docker-rmi":
        code, _, err = run(["docker", "rmi", a["id"]], timeout=300)
        return code == 0, err.strip(), None
    if op == "docker-volume-rm":
        code, _, err = run(["docker", "volume", "rm", a["name"]], timeout=120)
        return code == 0, err.strip(), None
    if op == "docker-network-rm":
        code, _, err = run(["docker", "network", "rm", a["name"]], timeout=60)
        return code == 0, err.strip(), None
    if op == "cmd":
        code, out, err = run(a["argv"], timeout=900)
        return code == 0, (err or out).strip()[-300:], None
    return False, f"unknown op {op}", None


def apply(plan: dict, repo: Repo, cfg: dict, only: Optional[Sequence[str]] = None, approve_s2: bool = False,
          confirm: Sequence[str] = (), dry_run: bool = False, force_kill: bool = False) -> Tuple[dict, int]:
    root = plan["root"]
    journal_path = os.path.join(state_dir(root, "journal", create=False),
                                f"{time.strftime('%Y%m%dT%H%M%S')}-{plan['level']}.jsonl")
    results = []
    drift = failed = 0
    confirm_set = set(confirm)
    rules = load_rules(root)
    # Worktrees go first: removing a clean worktree is what frees its landed branch for deletion.
    order = {"git-worktree-remove": 0, "git-worktree-prune": 0}
    for d in sorted(plan["items"], key=lambda x: order.get(x["op"], 1)):
        it = Item.from_dict({k: v for k, v in d.items() if k not in ("command", "policy")})
        if only and it.id not in only:
            continue
        rec = {"id": it.id, "op": it.op, "cls": it.cls, "kind": it.kind, "target": it.target, "undo": it.undo,
               "ts": time.time()}
        gate = None
        pv, prule = verdict(it, rules)
        rec["command"] = equivalent_command(it)
        if pv == "deny":
            rec.update(result="denied", detail=f"your permission rules deny this command ({prule}); not run")
            results.append(rec)
            continue
        if pv == "ask" and it.id not in confirm_set:
            gate = f"your permission rules ask before this command ({prule}): pass --confirm {it.id} only after the user approves it"
        elif it.cls == "S2" and not approve_s2:
            gate = "needs batch approval (S2): rerun with --approve-s2 after the user approves"
        elif it.cls == "S3" and it.id not in confirm_set:
            gate = "needs per-item confirmation (S3): pass --confirm " + it.id
        if gate:
            rec.update(result="gated", detail=gate)
            results.append(rec)
            continue
        if it.op in ("trash", "rm", "rm-children", "rm-files"):
            paths = it.args.get("files") or [it.args.get("path") or it.target]
            ok, why = True, ""
            for pth in paths:
                ok, why = _path_ok(root, pth, it.kind, cfg["protect"]["paths"])
                if not ok:
                    break
            if not ok:
                rec.update(result="refused", detail=why)
                results.append(rec)
                failed += 1
                continue
        ok, why = recheck(it, repo)
        if not ok:
            rec.update(result="drift", detail=why)
            results.append(rec)
            drift += 1
            continue
        if dry_run:
            rec.update(result="would-apply", detail="dry run")
            results.append(rec)
            continue
        try:
            ok, detail, undo_argv = execute(it, repo, force_kill=force_kill)
        except Exception as exc:  # one bad item must not abort the pass
            ok, detail, undo_argv = False, f"{type(exc).__name__}: {exc}", None
        rec.update(result="applied" if ok else "failed", detail=detail, bytes=it.size or 0)
        if undo_argv:
            rec["undo_argv"] = undo_argv
        if not ok:
            failed += 1
        results.append(rec)
        os.makedirs(os.path.dirname(journal_path), exist_ok=True)  # only when something was actually done
        with open(journal_path, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
    counts: Dict[str, int] = {}
    for r in results:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    reclaimed = sum(r.get("bytes", 0) for r in results if r["result"] == "applied")
    wrote = os.path.exists(journal_path)  # the journal exists only if something was actually done
    summary = {"level": plan["level"], "scope": plan.get("scope", "repo"), "journal": journal_path if wrote else None, "counts": counts,
               "reclaimed_bytes": reclaimed, "results": results}
    code = 6 if failed else (5 if drift else 0)
    return summary, code


def undo(journal: str, only: Optional[Sequence[str]] = None) -> Tuple[List[dict], int]:
    out = []
    code = 0
    with open(journal) as fh:
        entries = [json.loads(ln) for ln in fh if ln.strip()]
    for e in reversed(entries):
        if e.get("result") != "applied" or (only and e["id"] not in only):
            continue
        argv = e.get("undo_argv")
        if argv:
            c, _, err = run(argv, timeout=300)
            out.append({"id": e["id"], "undone": c == 0, "detail": err.strip(), "argv": argv})
            if c != 0:
                code = 6
        else:
            out.append({"id": e["id"], "undone": False, "detail": f"manual: {e.get('undo') or 'no undo recorded'}"})
    return out, code
