"""Subprocess, filesystem, and safety helpers shared by the collectors."""
from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
import time
from typing import List, Optional, Sequence, Tuple

# Paths that are never removed, whatever the level (spec R-4). Matched against the
# basename and against the path relative to the repo root.
PROTECTED_PATH_GLOBS = [
    ".git",
    ".git/*",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "id_ed25519*",
    "id_ecdsa*",
    ".quest",
    ".quest/*",
    ".lore",
    ".lore/*",
    "docs",
    "docs/*",
    ".pi",
    ".pi/*",
    ".housekeeping.toml",
]


def run(cmd: Sequence[str], cwd: Optional[str] = None, timeout: float = 60, check: bool = False) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            list(cmd), cwd=cwd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL
        )
    except FileNotFoundError:
        return 127, "", f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "", f"{cmd[0]}: timed out after {timeout}s"
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed ({p.returncode}): {p.stderr.strip()}")
    return p.returncode, p.stdout, p.stderr


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def match_any(name: str, globs: Sequence[str]) -> Optional[str]:
    for g in globs:
        if fnmatch.fnmatchcase(name, g):
            return g
    return None


def protected_path(rel: str, extra: Sequence[str] = ()) -> Optional[str]:
    """Return the matching protected glob for a repo-relative path, if any."""
    rel = rel.rstrip("/")
    base = os.path.basename(rel)
    globs = list(PROTECTED_PATH_GLOBS) + list(extra)
    for cand in (rel, base):
        hit = match_any(cand, globs)
        if hit:
            return hit
    # Any path inside a protected directory is protected too.
    parts = rel.split("/")
    for i in range(1, len(parts)):
        hit = match_any("/".join(parts[:i]), globs)
        if hit:
            return hit
    return None


def within(path: str, roots: Sequence[str]) -> bool:
    """True when the resolved path lies strictly inside one of the roots.

    A symlink is judged by where the link itself lives, not where it points:
    removing a link never touches its target.
    """
    p = os.path.abspath(path)
    parent = os.path.realpath(os.path.dirname(p))
    resolved = os.path.join(parent, os.path.basename(p))
    for r in roots:
        rr = os.path.realpath(r)
        if resolved != rr and resolved.startswith(rr.rstrip(os.sep) + os.sep):
            return True
    return False


def disk_usage(path: str, timeout: float = 30) -> Optional[int]:
    if os.path.islink(path) or os.path.isfile(path):
        try:
            return os.lstat(path).st_size
        except OSError:
            return None
    code, out, _ = run(["du", "-sk", path], timeout=timeout)
    if code != 0 or not out.strip():
        return None
    try:
        return int(out.split()[0]) * 1024
    except ValueError:
        return None


def age_days(path: str) -> Optional[float]:
    try:
        return round((time.time() - os.lstat(path).st_mtime) / 86400, 2)
    except OSError:
        return None


def file_fingerprint(path: str) -> dict:
    try:
        st = os.lstat(path)
    except OSError:
        return {"exists": False}
    return {"exists": True, "mtime_ns": st.st_mtime_ns, "size": st.st_size, "ino": st.st_ino}


def trash_command() -> Optional[List[str]]:
    """The platform trash tool, or None when only the manual fallback is available."""
    if os.environ.get("HK_TRASH_DIR"):
        return None
    for tool in ("/usr/bin/trash", "trash", "trash-put"):
        if os.path.isabs(tool) and os.access(tool, os.X_OK):
            return [tool]
        if not os.path.isabs(tool) and have(tool):
            return [tool]
    if have("gio"):
        return ["gio", "trash"]
    return None


def trash_available() -> bool:
    return trash_command() is not None or bool(os.environ.get("HK_TRASH_DIR"))


def fallback_trash_dir() -> str:
    d = os.environ.get("HK_TRASH_DIR") or os.path.expanduser("~/.local/share/housekeeping-trash")
    return os.path.join(d, time.strftime("%Y%m%dT%H%M%S"))


def parse_etime(etime: str) -> Optional[float]:
    """ps etime `[[dd-]hh:]mm:ss` -> seconds."""
    etime = etime.strip()
    if not etime:
        return None
    days = 0
    if "-" in etime:
        d, etime = etime.split("-", 1)
        days = int(d)
    parts = [int(x) for x in etime.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return days * 86400 + h * 3600 + m * 60 + s
