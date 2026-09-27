"""Git collectors: branches, remote branches, worktrees, stashes, and landing state.

The rule this module exists to enforce (spec R-5): a branch with unique commits
is unlanded work, not clutter. A branch is LANDED only on a containment proof
against the integration refs, never because its upstream is gone or its name
looks stale.
"""
from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional, Sequence, Tuple

from .model import Item
from .util import have, match_any, run


class Repo:
    def __init__(self, root: str, cfg: dict):
        self.root = root
        self.cfg = cfg
        self.remote = cfg["sdlc"].get("remote") or "origin"
        self.notes: List[str] = []

    def git(self, *args: str, timeout: float = 60) -> Tuple[int, str, str]:
        return run(["git", "-C", self.root, *args], timeout=timeout)

    def out(self, *args: str) -> str:
        code, out, _ = self.git(*args)
        return out.strip() if code == 0 else ""

    def ref_exists(self, ref: str) -> bool:
        return self.git("rev-parse", "--verify", "--quiet", ref + "^{commit}")[0] == 0

    def has_remote(self) -> bool:
        return self.remote in self.out("remote").split()

    # --- trunk detection -------------------------------------------------
    def branches_of_record(self) -> Tuple[str, Optional[str]]:
        """(trunk, release) branch names. Trunk is where work integrates."""
        sd = self.cfg["sdlc"]
        trunk = sd.get("trunk") or ""
        release = sd.get("release") or ""
        r = self.remote
        if not trunk:
            if self.ref_exists(f"refs/remotes/{r}/dev") or self.ref_exists("refs/heads/dev"):
                trunk = "dev"
            else:
                head = self.out("symbolic-ref", "--short", f"refs/remotes/{r}/HEAD")
                if head.startswith(r + "/"):
                    trunk = head[len(r) + 1 :]
                else:
                    for cand in ("main", "master", "trunk"):
                        if self.ref_exists(f"refs/heads/{cand}"):
                            trunk = cand
                            break
        if not release and trunk == "dev":
            for cand in ("main", "master"):
                if self.ref_exists(f"refs/remotes/{r}/{cand}") or self.ref_exists(f"refs/heads/{cand}"):
                    release = cand
                    break
        return trunk or "main", (release or None)

    def integration_refs(self) -> List[str]:
        """Refs a landed branch must be contained in (remote first; local fallback)."""
        trunk, release = self.branches_of_record()
        refs = []
        for b in (trunk, release):
            if not b:
                continue
            rr = f"refs/remotes/{self.remote}/{b}"
            if self.ref_exists(rr):
                refs.append(rr)
            elif self.ref_exists(f"refs/heads/{b}"):
                refs.append(f"refs/heads/{b}")
        return refs

    def current_branch(self) -> Optional[str]:
        return self.out("symbolic-ref", "--quiet", "--short", "HEAD") or None

    # --- containment proofs ----------------------------------------------
    def is_ancestor(self, a: str, b: str) -> bool:
        return self.git("merge-base", "--is-ancestor", a, b)[0] == 0

    def squash_equivalent(self, tip: str, target: str) -> Optional[bool]:
        """True when merging tip into target changes nothing (its content already landed).

        Uses `git merge-tree --write-tree` (git 2.38+). A conflict is not proof of
        anything, so it reports False; None means the check could not run.
        """
        code, out, _ = self.git("merge-tree", "--write-tree", target, tip)
        if code == 0:
            merged_tree = out.splitlines()[0].strip()
            return merged_tree == self.out("rev-parse", f"{target}^{{tree}}")
        if code == 1:
            return False
        return self._cherry_equivalent(tip, target)

    def _cherry_equivalent(self, tip: str, target: str) -> Optional[bool]:
        base = self.out("merge-base", target, tip)
        if not base:
            return None
        code, synthetic, _ = self.git("commit-tree", f"{tip}^{{tree}}", "-p", base, "-m", "hk squash probe")
        if code != 0:
            return None
        code, out, _ = self.git("cherry", target, synthetic.strip())
        if code != 0:
            return None
        return out.strip().startswith("-")

    def unique_commits(self, tip: str, target: str) -> int:
        try:
            return int(self.out("rev-list", "--count", f"{target}..{tip}") or 0)
        except ValueError:
            return 0

    # --- data sources ----------------------------------------------------
    def fetch_prune(self) -> bool:
        if not self.has_remote():
            self.notes.append("no remote configured: containment is proven against local branches only")
            return False
        code, _, err = self.git("fetch", "--prune", "--quiet", self.remote, timeout=120)
        if code != 0:
            self.notes.append(f"git fetch --prune failed ({err.strip()[:200]}): remote refs may be stale")
            return False
        return True

    def merged_prs(self) -> Dict[str, dict]:
        """headRefName -> merged PR, from gh when available. Empty when gh cannot answer."""
        if not have("gh") or not self.has_remote():
            return {}
        code, out, err = run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "merged",
                "--limit",
                "300",
                "--json",
                "number,headRefName,headRefOid,mergeCommit",
            ],
            cwd=self.root,
            timeout=60,
        )
        if code != 0:
            self.notes.append("gh could not list merged PRs; PR-state proof unavailable")
            return {}
        prs: Dict[str, dict] = {}
        try:
            for pr in json.loads(out or "[]"):
                prs.setdefault(pr.get("headRefName", ""), pr)
        except json.JSONDecodeError:
            return {}
        return prs

    def worktrees(self) -> List[dict]:
        out = self.out("worktree", "list", "--porcelain")
        wts: List[dict] = []
        cur: dict = {}
        for line in out.splitlines() + [""]:
            if not line:
                if cur:
                    wts.append(cur)
                cur = {}
                continue
            key, _, val = line.partition(" ")
            if key == "worktree":
                cur["path"] = val
            elif key == "HEAD":
                cur["head"] = val
            elif key == "branch":
                cur["branch"] = val.replace("refs/heads/", "", 1)
            elif key in ("locked", "prunable", "detached", "bare"):
                cur[key] = val or True
        for i, wt in enumerate(wts):
            wt["main"] = i == 0
        return wts

    def dirty_count(self, path: str) -> Optional[int]:
        code, out, _ = run(["git", "-C", path, "status", "--porcelain", "--untracked-files=normal"])
        if code != 0:
            return None
        return len([ln for ln in out.splitlines() if ln.strip()])


def prove_landed(repo: Repo, name: str, tip: str, targets: Sequence[str], prs: Dict[str, dict]) -> List[str]:
    """Containment proofs for a branch tip. Empty list means UNLANDED."""
    proofs: List[str] = []
    for t in targets:
        short = t.replace("refs/remotes/", "").replace("refs/heads/", "")
        if repo.is_ancestor(tip, t):
            proofs.append(f"ancestor of {short}")
            return proofs
    for t in targets:
        short = t.replace("refs/remotes/", "").replace("refs/heads/", "")
        if repo.squash_equivalent(tip, t):
            proofs.append(f"content already in {short} (merge-tree equals its tree)")
            return proofs
    pr = prs.get(name)
    if pr and pr.get("mergeCommit"):
        head = pr.get("headRefOid", "")
        merge = pr["mergeCommit"].get("oid", "")
        tip_in_pr = head == tip or (head and repo.is_ancestor(tip, head))
        if tip_in_pr and any(repo.is_ancestor(merge, t) for t in targets):
            proofs.append(f"PR #{pr.get('number')} MERGED and its merge commit is in the integration branch")
    return proofs


def collect(repo: Repo, ledger: dict, now: Optional[float] = None, fetch: bool = True, use_gh: bool = True) -> List[Item]:
    now = now or time.time()
    cfg = repo.cfg
    items: List[Item] = []
    if fetch:
        repo.fetch_prune()
    trunk, release = repo.branches_of_record()
    targets = repo.integration_refs()
    if not targets:
        repo.notes.append(f"integration branch {trunk!r} not found: no branch can be proven landed")
    prs = repo.merged_prs() if use_gh else {}
    current = repo.current_branch()
    wts = repo.worktrees()
    checked_out = {wt.get("branch"): wt for wt in wts if wt.get("branch")}
    protect_globs = list(cfg["protect"]["branches"])
    of_record = {b for b in (trunk, release, "main", "master", "dev") if b}
    ledger_branches = set(ledger.get("branch", {}))
    stale_days = float(cfg["branches"]["stale_days"])

    fmt = "%(refname:short)%00%(objectname)%00%(upstream:short)%00%(upstream:track)%00%(committerdate:unix)"
    for line in repo.out("for-each-ref", f"--format={fmt}", "refs/heads").splitlines():
        name, tip, upstream, track, cdate = (line.split("\0") + [""] * 5)[:5]
        age = round((now - int(cdate or now)) / 86400, 2)
        prov = "ledger" if name in ledger_branches else "unknown"
        base = dict(domain="git", target=f"refs/heads/{name}", provenance=prov, age_days=age)
        fp = {"tip": tip}
        if name in of_record:
            continue  # branches of record are not inventory, they are the reference
        why_protected = None
        if name == current:
            why_protected = "checked out in the main worktree"
        elif name in checked_out and not checked_out[name].get("main"):
            why_protected = f"checked out in worktree {checked_out[name]['path']}"
        else:
            g = match_any(name, protect_globs)
            if g:
                why_protected = f"reserved prefix {g} (deliberate preservation)"
        proofs = prove_landed(repo, name, tip, targets, prs) if targets else []
        evidence = list(proofs)
        if track == "[gone]":
            evidence.append("upstream deleted on the remote (evidence only, not a containment proof)")
        if proofs:
            items.append(
                Item(
                    kind="branch.landed",
                    level="C3",
                    cls="S1",
                    op="git-branch-delete",
                    reason=f"landed: {proofs[0]}",
                    args={"name": name},
                    undo=f"git branch {name} {tip}",
                    evidence=evidence,
                    fingerprint=fp,
                    protected=why_protected,
                    **base,
                )
            )
            continue
        uniq = repo.unique_commits(tip, targets[0]) if targets else 0
        evidence.append(f"{uniq} commit(s) not in {targets[0] if targets else 'any integration branch'}")
        if why_protected:
            items.append(
                Item(kind="branch.unlanded", level="C1", cls="S0", op="report",
                     reason=f"unlanded, kept: {why_protected}", evidence=evidence, fingerprint=fp,
                     protected=why_protected, **base)
            )
        elif age >= stale_days:
            items.append(
                Item(
                    kind="branch.stale-unlanded",
                    level="C4",
                    cls="S3",
                    op="git-archive-branch",
                    reason=f"UNLANDED work, idle {age:.0f} days: archive ref first, then delete (confirm by name)",
                    args={"name": name, "archive_ref": f"refs/tags/archive/{name}"},
                    undo=f"git branch {name} {tip}   # also kept at refs/tags/archive/{name}",
                    evidence=evidence,
                    fingerprint=fp,
                    **base,
                )
            )
        else:
            items.append(
                Item(kind="branch.unlanded", level="C3", cls="S0", op="report",
                     reason="UNLANDED work: land it or record why it is dropped", evidence=evidence,
                     fingerprint=fp, **base)
            )

    # Remote branches: only landed ones are ever planned; unlanded ones may be someone else's work.
    if targets and repo.has_remote():
        rfmt = "%(refname)%00%(objectname)%00%(committerdate:unix)"
        r = repo.remote
        for line in repo.out("for-each-ref", f"--format={rfmt}", f"refs/remotes/{r}").splitlines():
            ref, tip, cdate = (line.split("\0") + [""] * 3)[:3]
            name = ref[len(f"refs/remotes/{r}/") :]
            if name == "HEAD" or name in of_record:
                continue
            base = dict(domain="git", target=ref, provenance="unknown",
                        age_days=round((now - int(cdate or now)) / 86400, 2))
            g = match_any(name, protect_globs)
            proofs = prove_landed(repo, name, tip, targets, prs)
            if proofs:
                items.append(
                    Item(kind="remote-branch.landed", level="C3", cls="S1", op="git-push-delete",
                         reason=f"remote branch landed: {proofs[0]}", args={"remote": r, "name": name},
                         undo=f"git push {r} {tip}:refs/heads/{name}", evidence=proofs,
                         fingerprint={"tip": tip}, protected=(f"reserved prefix {g}" if g else None), **base)
                )
            else:
                items.append(
                    Item(kind="remote-branch.unlanded", level="C3", cls="S0", op="report",
                         reason="remote branch with unlanded commits (not ours to delete)", fingerprint={"tip": tip}, **base)
                )

    # Worktrees
    ledger_wts = set(ledger.get("worktree", {}))
    for wt in wts:
        if wt.get("main") or wt.get("bare"):
            continue
        path = wt["path"]
        prov = "ledger" if path in ledger_wts else ("attributed" if "/.claude/worktrees/" in path else "unknown")
        base = dict(domain="git", target=path, provenance=prov)
        if wt.get("prunable"):
            items.append(
                Item(kind="worktree.prunable", level="C3", cls="S1", op="git-worktree-prune",
                     reason=f"worktree metadata for a missing directory ({wt['prunable']})",
                     undo="none needed: the directory is already gone", fingerprint={"exists": False}, **base)
            )
            continue
        if wt.get("locked"):
            items.append(
                Item(kind="worktree.locked", level="C3", cls="S0", op="report",
                     reason=f"locked worktree ({wt['locked']}): unlock deliberately if it is done", **base)
            )
            continue
        dirty = repo.dirty_count(path)
        fp = {"head": wt.get("head"), "dirty": dirty}
        if dirty:
            items.append(
                Item(kind="worktree.dirty", level="C2", cls="S0", op="report",
                     reason=f"{dirty} uncommitted change(s): work hides here, land it first",
                     fingerprint=fp, **base)
            )
            continue
        branch = wt.get("branch")
        landed = bool(branch) and bool(targets) and bool(prove_landed(repo, branch, wt.get("head", ""), targets, prs))
        level = "C2" if prov == "ledger" else "C3"
        items.append(
            Item(kind="worktree.clean", level=level, cls="S1", op="git-worktree-remove",
                 reason=("clean worktree of a landed branch" if landed else "clean worktree; its branch and commits stay"),
                 args={"path": path, "branch": branch},
                 undo=(f"git worktree add {path} {branch}" if branch else f"git worktree add --detach {path} {wt.get('head')}"),
                 evidence=["no uncommitted or untracked changes", "ignored files inside it (e.g. node_modules) are regenerable"],
                 fingerprint=fp, **base)
        )

    # Stashes
    max_age = float(cfg["stash"]["max_age_days"])
    out = repo.out("stash", "list", "--format=%H%x00%ct%x00%gd%x00%gs")
    for line in out.splitlines():
        sha, ct, ref, subj = (line.split("\0") + [""] * 4)[:4]
        age = round((now - int(ct or now)) / 86400, 2)
        base = dict(domain="git", target=f"stash {sha[:12]}", provenance="unknown", age_days=age, fingerprint={"sha": sha})
        if age >= max_age:
            items.append(
                Item(kind="stash.old", level="C4", cls="S1", op="git-stash-archive-drop",
                     reason=f"stash idle {age:.0f} days ({subj[:60]}): keep it under refs/archive, then drop",
                     args={"sha": sha, "message": subj}, undo=f"git stash store -m {json.dumps(subj)} {sha}", **base)
            )
        else:
            items.append(Item(kind="stash.recent", level="C2", cls="S0", op="report",
                              reason=f"stash to review: {ref} {subj[:60]}", **base))
    return items


def status(repo: Repo) -> dict:
    """Landing state for the Record and Land phases (read-only)."""
    trunk, release = repo.branches_of_record()
    cur = repo.current_branch()
    porcelain = repo.out("status", "--porcelain", "--untracked-files=all")
    changes = [ln for ln in porcelain.splitlines() if ln.strip()]
    ahead = behind = None
    upstream = repo.out("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") or None
    if upstream:
        lr = repo.out("rev-list", "--left-right", "--count", f"{upstream}...HEAD").split()
        if len(lr) == 2:
            behind, ahead = int(lr[0]), int(lr[1])
    findings = []
    if cur in (trunk, release):
        findings.append(f"HEAD is on {cur}: commit on a task branch, never on {trunk}/{release or 'release'}")
    if cur and not upstream:
        findings.append(f"branch {cur} has no upstream: push it with -u")
    if ahead:
        findings.append(f"{ahead} commit(s) not pushed")
    return {
        "root": repo.root,
        "branch": cur,
        "trunk": trunk,
        "release": release,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "uncommitted": len(changes),
        "changes": changes[:200],
        "findings": findings,
        "notes": repo.notes,
    }
