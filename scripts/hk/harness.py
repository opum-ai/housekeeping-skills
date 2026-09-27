"""Claude Code harness collectors (user level, C4+) and global dev caches (C5).

Removals here use Claude Code's own commands where one exists
(`claude project purge`, `claude plugin prune`), so the harness stays the owner
of its state. Context-bloat and permission findings are proposals only: the
skill reviews them with the user; the engine never edits settings or memory.
"""
from __future__ import annotations

import glob
import json
import os
import re
from typing import Dict, List, Optional

from .model import Item
from .util import disk_usage, file_fingerprint, have, run

HOME = os.path.expanduser("~")
CLAUDE = os.path.join(HOME, ".claude")

BROAD_RULES = [
    r"^Bash$", r"^Bash\(\*\)$", r"^Bash\((rm|sudo|bash|sh|zsh|eval|curl|wget)[ :]\*?\)", r"^Bash\(rm -rf",
    r"^mcp__\*$", r"^Write$", r"^Write\(\*\*?\)$",
]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def claude_home() -> str:
    """Claude Code's config dir: CLAUDE_CONFIG_DIR relocates ~/.claude (HK_CLAUDE_HOME overrides for tests)."""
    return os.environ.get("HK_CLAUDE_HOME") or os.environ.get("CLAUDE_CONFIG_DIR") or CLAUDE


def collect_plugin_cache(sizes: bool = True) -> List[Item]:
    items: List[Item] = []
    cache = os.path.join(claude_home(), "plugins", "cache")
    for ver_dir in sorted(glob.glob(os.path.join(cache, "*", "*", "*"))):
        if not os.path.isdir(ver_dir):
            continue
        in_use = os.path.join(ver_dir, ".in_use")
        live, dead = [], []
        if os.path.isdir(in_use):
            for name in os.listdir(in_use):
                if name.isdigit():
                    (live if _pid_alive(int(name)) else dead).append(os.path.join(in_use, name))
        rel = os.path.relpath(ver_dir, cache)
        if dead:
            items.append(Item(domain="harness", kind="plugin.stale-in-use", target=in_use, level="deep", scope="machine", cls="S2",
                              op="rm-files", args={"files": dead, "pid_markers": True}, provenance="attributed",
                              fingerprint={"count": len(dead)},
                              reason=f"{len(dead)} in-use marker(s) for dead processes on {rel} (can pin an outdated plugin version)",
                              undo="none needed: Claude Code rewrites markers for live sessions"))
        if os.path.exists(os.path.join(ver_dir, ".orphaned_at")):
            items.append(Item(domain="harness", kind="plugin.orphaned-version", target=ver_dir, level="deep", scope="machine", cls="S2",
                              op="rm", provenance="attributed", size=disk_usage(ver_dir) if sizes else None,
                              fingerprint=file_fingerprint(ver_dir),
                              protected=("a live session still uses it" if live else None),
                              reason=f"plugin version {rel} marked orphaned by Claude Code",
                              undo="reinstall that version from its marketplace if ever needed"))
    return items


def _transcript_cwd(project_dir: str) -> Optional[str]:
    for jf in sorted(glob.glob(os.path.join(project_dir, "*.jsonl")))[:3]:
        try:
            with open(jf, encoding="utf-8", errors="replace") as fh:
                for _ in range(40):
                    line = fh.readline()
                    if not line:
                        break
                    if '"cwd"' in line:
                        try:
                            cwd = json.loads(line).get("cwd")
                        except json.JSONDecodeError:
                            continue
                        if cwd:
                            return cwd
        except OSError:
            continue
    return None


def collect_projects(sizes: bool = True) -> List[Item]:
    """Transcript dirs whose project path no longer exists -> `claude project purge` (S3)."""
    items: List[Item] = []
    pdir = os.path.join(claude_home(), "projects")
    if not os.path.isdir(pdir):
        return items
    for d in sorted(os.listdir(pdir)):
        full = os.path.join(pdir, d)
        if not os.path.isdir(full):
            continue
        cwd = _transcript_cwd(full)
        if not cwd or os.path.exists(cwd):
            continue
        # `claude project purge <path>` finds state by the slug of the path. Use it only when this
        # directory really is that slug; otherwise the purge would silently find nothing.
        slug = re.sub(r"[^A-Za-z0-9]", "-", cwd)
        if d == slug:
            op, args = "cmd", {"argv": ["claude", "project", "purge", cwd, "-y"]}
            undo = "none: transcripts are deleted (export first with /export if any matter)"
        else:
            op, args = "trash", {}
            undo = "restore from the Trash"
        items.append(Item(domain="harness", kind="project.missing-path", target=(cwd if op == "cmd" else full),
                          level="deep", scope="machine", cls="S3", op=op, args=args, provenance="attributed",
                          size=disk_usage(full) if sizes else None,
                          fingerprint=({"exists": False} if op == "cmd" else file_fingerprint(full)),
                          evidence=[f"transcripts in {full}", f"project path {cwd} no longer exists"],
                          reason="transcripts, tasks, and file history for a project whose directory is gone",
                          undo=undo))
    return items


def _lines(path: str) -> int:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def collect_context(root: str, slugs: List[str]) -> List[Item]:
    """Context-cost findings: always-loaded instruction and memory files that grew too big."""
    items: List[Item] = []
    checks = [(os.path.join(root, "CLAUDE.md"), 300), (os.path.join(root, "AGENTS.md"), 300),
              (os.path.join(claude_home(), "CLAUDE.md"), 200)]
    for slug in slugs:
        checks.append((os.path.join(claude_home(), "projects", slug, "memory", "MEMORY.md"), 150))
    for path, limit in checks:
        n = _lines(path)
        if n > limit:
            items.append(Item(domain="harness", kind="context.large-file", target=path, level="deep",
                              scope="machine" if path.startswith(claude_home() + os.sep) and "/projects/" not in path else "repo", cls="S0",
                              op="report", size=os.path.getsize(path), provenance="attributed",
                              reason=f"{n} lines loaded into every session (guide: <= {limit}); move detail into skills or linked files",
                              evidence=[f"{n} lines"]))
    for slug in slugs:
        mem = os.path.join(claude_home(), "projects", slug, "memory")
        for mf in sorted(glob.glob(os.path.join(mem, "*.md"))):
            if os.path.basename(mf) == "MEMORY.md":
                continue
            try:
                text = open(mf, encoding="utf-8", errors="replace").read(20000)
            except OSError:
                continue
            if re.search(r"\b(superseded|obsolete|no longer (true|applies)|deprecated)\b", text, re.I):
                items.append(Item(domain="harness", kind="memory.superseded", target=mf, level="deep", cls="S0",
                                  op="report", provenance="attributed",
                                  reason="memory marks itself superseded: fold it into its successor or delete it (with the user)"))
    return items


def collect_settings(root: str) -> List[Item]:
    items: List[Item] = []
    files = [os.path.join(claude_home(), "settings.json"), os.path.join(claude_home(), "settings.local.json"),
             os.path.join(root, ".claude", "settings.json"), os.path.join(root, ".claude", "settings.local.json")]
    for f in files:
        try:
            data = json.load(open(f))
        except (OSError, json.JSONDecodeError):
            continue
        allow = (data.get("permissions") or {}).get("allow") or []
        flagged: List[str] = []
        bad: set = set()
        for rule in allow:
            reasons = []
            if any(re.search(p, rule) for p in BROAD_RULES):
                reasons.append("overly broad")
            if re.search(r"\b[0-9a-f]{40}\b", rule):
                reasons.append("pins a commit SHA (one-off)")
            if re.search(r"/(issues|pull)/\d+", rule):
                reasons.append("names one issue/PR (one-off)")
            if re.search(r"gh api (-X|--method) (POST|PUT|PATCH|DELETE)", rule):
                reasons.append("standing approval for a write to remote state")
            for p in re.findall(r"(/(?:Users|home|Volumes|private|tmp)/[^\s:*)\"']+)", rule):
                if not os.path.exists(p.rstrip("/")):
                    reasons.append(f"path no longer exists ({p})")
                    break
            if reasons:
                bad.add(rule)
                flagged.append(f"{rule}  <- {', '.join(reasons)}")
        for fam, members in _families(allow):
            bad.update(members)
            flagged.append(f"{len(members)} rules differ only in one argument ({fam}): likely one rollout, consolidate or drop")
        if flagged:
            items.append(Item(domain="harness", kind="settings.permission-rules", target=f, level="deep",
                              scope="machine" if f.startswith(claude_home() + os.sep) else "repo", cls="S0",
                              op="report", provenance="attributed", evidence=flagged[:40],
                              reason=f"{len(bad)} of {len(allow)} allow rules look one-off, stale, or too broad"))
        hooks = data.get("hooks") or {}
        n_hooks = sum(len(m.get("hooks", [])) for ev in hooks.values() if isinstance(ev, list) for m in ev if isinstance(m, dict))
        if n_hooks > 10:
            items.append(Item(domain="harness", kind="settings.many-hooks", target=f, level="deep",
                              scope="machine" if f.startswith(claude_home() + os.sep) else "repo", cls="S0", op="report",
                              provenance="attributed", reason=f"{n_hooks} hooks configured: review with /hooks for slow or redundant ones"))
    return items


def _families(rules: List[str], min_size: int = 4) -> List[tuple]:
    """Groups of rules identical except for one token, e.g. the same command per repo."""
    groups: Dict[tuple, set] = {}
    for rule in rules:
        toks = re.split(r"([/ :])", rule)
        for i, t in enumerate(toks):
            if t in ("/", " ", ":", "", "*"):
                continue
            key = tuple(toks[:i]) + ("<*>",) + tuple(toks[i + 1:])
            groups.setdefault(key, set()).add(rule)
    out, used = [], set()
    for key, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        fresh = members - used
        if len(fresh) >= min_size:
            out.append(("".join(key), sorted(fresh)))
            used |= fresh
    return out


def collect_duplicate_skills(root: str) -> List[Item]:
    items: List[Item] = []
    local = {os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(root, ".claude", "skills", "*", "SKILL.md"))}
    if not local:
        return items
    try:
        installed = json.load(open(os.path.join(claude_home(), "plugins", "installed_plugins.json")))
    except (OSError, json.JSONDecodeError):
        return items
    for key, entries in (installed.get("plugins") or {}).items():
        for e in entries if isinstance(entries, list) else [entries]:
            path = (e or {}).get("installPath", "")
            for sk in glob.glob(os.path.join(path, "skills", "*", "SKILL.md")):
                name = os.path.basename(os.path.dirname(sk))
                if name in local:
                    items.append(Item(domain="harness", kind="skills.duplicate", target=os.path.join(root, ".claude", "skills", name),
                                      level="deep", cls="S0", op="report", provenance="attributed",
                                      reason=f"skill {name!r} is listed twice: repo copy and plugin {key} (both cost context)"))
    return items


# name, probe path(s), prune argv
CACHES = [
    ("npm", ["~/.npm/_cacache"], ["npm", "cache", "clean", "--force"]),
    ("bun", ["~/.bun/install/cache"], ["bun", "pm", "cache", "rm"]),
    ("pnpm", ["~/Library/pnpm/store", "~/.local/share/pnpm/store"], ["pnpm", "store", "prune"]),
    ("yarn", ["~/Library/Caches/Yarn", "~/.cache/yarn"], ["yarn", "cache", "clean"]),
    ("uv", ["~/.cache/uv", "~/Library/Caches/uv"], ["uv", "cache", "prune"]),
    ("pip", ["~/Library/Caches/pip", "~/.cache/pip"], ["pip3", "cache", "purge"]),
    ("go", ["~/Library/Caches/go-build", "~/.cache/go-build"], ["go", "clean", "-cache"]),
    ("brew", ["~/Library/Caches/Homebrew"], ["brew", "cleanup", "-s"]),
]


def collect_caches(sizes: bool = True) -> List[Item]:
    items: List[Item] = []
    for name, probes, argv in CACHES:
        path = next((os.path.expanduser(p) for p in probes if os.path.isdir(os.path.expanduser(p))), None)
        if not path or not have(argv[0]):
            continue
        items.append(Item(domain="caches", kind="cache.global", target=path, level="deep", scope="machine", cls="S2", op="cmd",
                          args={"argv": argv}, provenance="unknown", size=disk_usage(path, timeout=90) if sizes else None,
                          reason=f"{name} cache, pruned with its own command", undo="re-downloaded on the next install"))
    dd = os.path.expanduser("~/Library/Developer/Xcode/DerivedData")
    if os.path.isdir(dd) and os.listdir(dd):
        items.append(Item(domain="caches", kind="cache.xcode", target=dd, level="deep", scope="machine", cls="S2", op="rm-children",
                          args={"path": dd}, provenance="unknown", size=disk_usage(dd, timeout=90) if sizes else None,
                          reason="Xcode DerivedData", undo="rebuilt by Xcode on the next build"))
    return items
