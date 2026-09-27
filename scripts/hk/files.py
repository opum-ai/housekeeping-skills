"""File collectors: agent junk, build outputs, temp dirs, session scratchpads, clean room.

Nothing tracked by git is ever a candidate, and the protected path set (spec
R-4, e.g. `.env*`) is reported but never planned. Agent junk is recognised by
name, but a junk-looking file this session did not create is raised a class:
the name alone is not evidence that nobody wants it.
"""
from __future__ import annotations

import os
import re
import tempfile
import time
from typing import List, Optional, Set

from .model import Item, raise_class
from .util import age_days, disk_usage, file_fingerprint, match_any, protected_path, run, trash_available

# Names coding agents (and people) leave behind. Matched against the basename of
# untracked files only. Deliberately excludes plausible real work such as *_v2.py
# in a src tree: those match only when untracked AND the reviewer approves.
JUNK_GLOBS = [
    "*.bak", "*.bak.*", "*.orig", "*.rej", "*.tmp", "*.temp", "*~", "*.swp", "*.swo",
    ".DS_Store", "Thumbs.db", "desktop.ini",
    "*_old", "*_old.*", "*.old", "*_backup", "*_backup.*", "*.backup",
    "*_v[0-9]", "*_v[0-9].*", "*_v[0-9][0-9].*", "* copy", "* copy.*", "* copy [0-9]*", "* ([0-9])*",
    "tmp_*", "temp_*", "scratch", "scratch.*", "scratch_*", "scratch-*",
    "debug.log", "debug-*.log", "debug_*.log", "*.log", "npm-debug.log*", "yarn-error.log*", "nohup.out",
    "core", "core.[0-9]*", "nul", "NUL",
    "*_SUMMARY.md", "SUMMARY_*.md", "*_REPORT.md", "IMPLEMENTATION_*.md", "FIXES*.md", "CHANGES_*.md",
    "test_output*", "output.txt", "out.txt",
]

# Ignored directories that a package manager or build regenerates (S2).
BUILD_DIRS = {
    "node_modules", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".turbo", ".parcel-cache",
    ".vite", ".angular", "coverage", ".nyc_output", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", ".venv", "venv", "target", ".gradle", ".build", "DerivedData",
    ".hypothesis", ".eggs", "storybook-static", ".expo", ".dart_tool", ".cache", "htmlcov",
}
BUILD_SUFFIXES = (".egg-info",)
BUILD_FILES = {".coverage", "coverage.xml", ".eslintcache", "tsconfig.tsbuildinfo"}


def _is_build(rel: str) -> bool:
    base = os.path.basename(rel.rstrip("/"))
    return base in BUILD_DIRS or base in BUILD_FILES or base.endswith(BUILD_SUFFIXES)


def _git_list(root: str, *args: str) -> List[str]:
    code, out, _ = run(["git", "-C", root, *args], timeout=120)
    if code != 0:
        return []
    return [p for p in out.split("\0") if p]


def untracked(root: str) -> List[str]:
    return _git_list(root, "ls-files", "--others", "--exclude-standard", "-z")


def ignored(root: str) -> List[str]:
    """Ignored paths with ignored directories collapsed to one entry (trailing /)."""
    return _git_list(root, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z")


def _trash_class(prov: str) -> str:
    base = "S1" if trash_available() else "S2"
    return base if prov == "ledger" else raise_class(base)


def collect(root: str, cfg: dict, ledger: dict, level: str, sizes: bool = True) -> List[Item]:
    items: List[Item] = []
    junk_globs = JUNK_GLOBS + list(cfg["junk"]["patterns"])
    extra_protect = list(cfg["protect"]["paths"])
    keep = list(cfg["immaculate"]["keep"])
    ledger_files: Set[str] = set(ledger.get("file", {}))
    seen: Set[str] = set()

    def prov_of(abs_path: str) -> str:
        return "ledger" if abs_path in ledger_files else "unknown"

    def size_of(p: str) -> Optional[int]:
        return disk_usage(p) if sizes else None

    # Untracked (not ignored) files: junk by name, else real uncommitted work.
    for rel in untracked(root):
        ap = os.path.join(root, rel)
        prot = protected_path(rel, extra_protect)
        base = os.path.basename(rel)
        hit = match_any(base, junk_globs)
        prov = prov_of(ap)
        common = dict(domain="files", target=ap, provenance=prov, age_days=age_days(ap),
                      fingerprint=file_fingerprint(ap), protected=prot)
        if hit:
            seen.add(rel)
            cls = _trash_class(prov)
            items.append(
                Item(kind="file.junk", level="light" if prov == "ledger" else "standard", cls=cls, op="trash", size=size_of(ap),
                     reason=f"untracked, matches agent-junk pattern {hit}"
                     + ("" if prov == "ledger" else " (not recorded as created by a session: review)"),
                     undo="restore from the Trash (Finder: Put Back)", evidence=[f"pattern {hit}", f"provenance {prov}"],
                     **common)
            )
        elif prov == "ledger":
            seen.add(rel)
            items.append(
                Item(kind="file.untracked-work", level="minimal", cls="S0", op="report",
                     reason="created this session and not committed: commit it or say why not", **common)
            )
        else:
            items.append(
                Item(kind="file.untracked", level="immaculate", cls="S3", op="trash", size=size_of(ap),
                     reason="untracked, not ignored, not recognisable junk: possibly someone's work (needs a disposition: commit, ignore, keep, or remove)",
                     undo="restore from the Trash (Finder: Put Back)", **common)
            )
            seen.add(rel)

    # Ignored entries: build outputs (C4, S2), ignored junk (C3), everything else only in the clean room.
    for rel in ignored(root):
        rel_clean = rel.rstrip("/")
        ap = os.path.join(root, rel_clean)
        if rel_clean in seen:
            continue
        prot = protected_path(rel_clean, extra_protect)
        kept = match_any(os.path.basename(rel_clean), keep) or match_any(rel_clean, keep)
        if kept and not prot:
            prot = f"immaculate keep-list ({kept})"
        base = os.path.basename(rel_clean)
        common = dict(domain="files", target=ap, provenance=("ledger" if ap in ledger_files else "attributed"),
                      age_days=age_days(ap), fingerprint=file_fingerprint(ap), protected=prot)
        if _is_build(rel_clean):
            items.append(
                Item(kind="dir.build" if rel.endswith("/") else "file.build", level="deep", cls="S2", op="rm",
                     size=size_of(ap), reason=f"ignored build/dependency output ({base}): regenerated by install/build",
                     undo="re-run the project's install/build", **common)
            )
        elif match_any(base, junk_globs):
            items.append(
                Item(kind="file.junk-ignored", level="standard", cls="S1" if trash_available() else "S2", op="trash",
                     size=size_of(ap), reason=f"ignored and matches an agent-junk pattern", undo="restore from the Trash",
                     **common)
            )
        else:
            items.append(
                Item(kind="file.ignored-other", level="immaculate", cls="S3", op="trash", size=size_of(ap),
                     reason="ignored but not a known build output (could be local config): needs a disposition, removal only if confirmed by name",
                     undo="restore from the Trash", **common)
            )
    return items


def collect_tmp(root: str, cfg: dict, ledger: dict, sizes: bool = True, now: Optional[float] = None) -> List[Item]:
    """$TMPDIR entries attributed to this repo by configured prefix, or by the ledger."""
    now = now or time.time()
    items: List[Item] = []
    tmp = os.path.realpath(tempfile.gettempdir())
    prefixes = list(cfg["tmp"]["prefixes"])
    max_age = float(cfg["tmp"]["max_age_days"])
    ledger_paths = set(ledger.get("file", {})) | set(ledger.get("dir", {}))
    try:
        names = os.listdir(tmp)
    except OSError:
        return items
    for name in names:
        ap = os.path.join(tmp, name)
        in_ledger = ap in ledger_paths or os.path.join(tempfile.gettempdir(), name) in ledger_paths
        pref = next((p for p in prefixes if name.startswith(p)), None)
        if not (in_ledger or pref):
            continue
        age = age_days(ap) or 0.0
        if not in_ledger and age < max_age:
            continue
        items.append(
            Item(domain="files", kind="tmp.attributed", target=ap, level="light" if in_ledger else "deep",
                 cls="S2", op="rm", provenance="ledger" if in_ledger else "attributed",
                 size=disk_usage(ap) if sizes else None, age_days=age, fingerprint=file_fingerprint(ap),
                 reason=(f"temp entry created this session" if in_ledger else f"temp entry with prefix {pref!r}, idle {age:.1f} days"),
                 undo="none: temp data (regenerated by the run that made it)")
        )
    return items


def scratchpad_root() -> str:
    return f"/private/tmp/claude-{os.getuid()}" if os.path.isdir("/private/tmp") else f"/tmp/claude-{os.getuid()}"


def project_slugs(root: str) -> List[str]:
    """Claude Code names a project dir after its launch path with '/' -> '-'."""
    cands = {root, os.path.realpath(root), os.path.abspath(root)}
    return sorted({re.sub(r"[^A-Za-z0-9]", "-", c) for c in cands})


def collect_scratchpads(root: str, cfg: dict, level: str, sizes: bool = True) -> List[Item]:
    """Old Claude Code session scratch dirs. C4: this project's; C5: every project's."""
    items: List[Item] = []
    sroot = scratchpad_root()
    if not os.path.isdir(sroot):
        return items
    current = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    max_age = float(cfg["scratchpad"]["max_age_days"])
    mine = set(project_slugs(root))
    for proj in sorted(os.listdir(sroot)):
        pdir = os.path.join(sroot, proj)
        if not os.path.isdir(pdir):
            continue
        is_mine = proj in mine
        for sess in sorted(os.listdir(pdir)):
            sdir = os.path.join(pdir, sess)
            if not os.path.isdir(sdir):
                continue
            age = _newest_mtime_age(sdir)
            prot = "current session" if current and sess == current else None
            if age is None or (age < max_age and not prot):
                continue
            items.append(
                Item(domain="harness", kind="scratchpad.old", target=sdir, level="deep", scope="repo" if is_mine else "machine",
                     cls="S2", op="rm", provenance="attributed", size=disk_usage(sdir) if sizes else None,
                     age_days=age, fingerprint=file_fingerprint(sdir), protected=prot,
                     reason=f"Claude Code session scratch dir idle {age:.1f} days" + ("" if is_mine else " (another project)"),
                     undo="none: session scratch output")
            )
    return items


def _newest_mtime_age(path: str, limit: int = 2000) -> Optional[float]:
    newest = 0.0
    n = 0
    for dp, dns, fns in os.walk(path):
        for f in fns + dns:
            try:
                newest = max(newest, os.lstat(os.path.join(dp, f)).st_mtime)
            except OSError:
                pass
            n += 1
            if n >= limit:
                break
        if n >= limit:
            break
    if newest == 0.0:
        try:
            newest = os.lstat(path).st_mtime
        except OSError:
            return None
    return round((time.time() - newest) / 86400, 2)
