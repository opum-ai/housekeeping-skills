"""Runtime collectors: Docker containers, images, volumes, networks, build cache, processes.

Scope comes from evidence, never from "looks unused":
- a container is this project's when its compose project label matches, or the
  provenance ledger recorded it;
- a process is this repo's when its working directory is inside the repo, or
  the ledger recorded its command.
The protected set (e.g. the self-hosted CI runner `opum-runner`) is matched by
name and by image in whatever Docker context is active.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Dict, List, Optional, Set

from .model import Item
from .util import have, match_any, parse_etime, run

DEV_PROC = re.compile(
    r"(^|/)(node|bun|deno|npm|npx|pnpm|yarn|python[0-9.]*|uvicorn|gunicorn|flask|vite|next|nuxt|webpack|"
    r"esbuild|tsx|ts-node|nodemon|ruby|rails|puma|air|java|gradle|mvn|cargo|quest|lore|http-server|serve|jupyter[-a-z]*)$"
)
NEVER_KILL = [
    "*pm2*", "*PM2*", "*hermes*", "*Runner.Listener*", "*actions-runner*", "*opum-runner*",
    "*language-server*", "*languageserver*", "*tsserver*", "*gopls*", "*rust-analyzer*", "*copilot*",
    "*Code Helper*", "*launchd*", "*orbstack*", "*docker*",
]


def _is_dev(cmd: str) -> bool:
    """A developer process we may reason about: a runtime or dev server, never an app or daemon we know."""
    argv0 = cmd.split()[0]
    base = os.path.basename(argv0)
    is_python = base.lower().startswith("python")
    if not (DEV_PROC.search(argv0) or is_python):
        return False
    if match_any(cmd, NEVER_KILL) or base == "claude":
        return False
    # GUI app bundles carry their own node/python helpers; the Python.app framework stub is the exception.
    return not (".app/Contents/" in argv0 and not is_python)


def _compose_name(root: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "", os.path.basename(os.path.realpath(root)).lower())


def _labels(s: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for part in (s or "").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k] = v
    return out


def _docker_json(args: List[str]) -> List[dict]:
    code, out, _ = run(["docker", *args], timeout=30)
    if code != 0:
        return []
    rows = []
    for line in out.splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def _size_bytes(s: str) -> Optional[int]:
    m = re.match(r"([\d.]+)\s*([kKMGT]?B)", s or "")
    if not m:
        return None
    mult = {"B": 1, "kB": 1e3, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12}[m.group(2)]
    return int(float(m.group(1)) * mult)


def docker_available() -> bool:
    return have("docker") and run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=15)[0] == 0


def collect_docker(root: str, cfg: dict, ledger: dict, notes: List[str]) -> List[Item]:
    items: List[Item] = []
    if not docker_available():
        notes.append("docker not available or daemon not running: container cleanup skipped")
        return items
    ctx = run(["docker", "context", "show"], timeout=10)[1].strip()
    if ctx:
        notes.append(f"docker context: {ctx} (other contexts were not inspected)")
    projects = set(cfg["docker"]["projects"]) or {_compose_name(root)}
    pc, pi = list(cfg["protect"]["containers"]), list(cfg["protect"]["images"])
    ledger_c = set(ledger.get("container", {}))

    used_images: Set[str] = set()
    containers = _docker_json(["ps", "-a", "--no-trunc", "--format", "{{json .}}"])
    for c in containers:
        cid, names, image = c.get("ID", ""), c.get("Names", ""), c.get("Image", "")
        state = (c.get("State") or "").lower()
        labels = _labels(c.get("Labels", ""))
        used_images.add(image)
        proj = labels.get("com.docker.compose.project", "")
        prot = None
        if match_any(names, pc) or match_any(image, pi) or labels.get("housekeeping.protect") == "true":
            prot = "protected container (e.g. the self-hosted CI runner)"
        prov = "ledger" if (cid in ledger_c or names in ledger_c) else ("attributed" if proj in projects else "unknown")
        base = dict(domain="runtime", target=cid[:12], provenance=prov, protected=prot,
                    fingerprint={"id": cid, "state": state},
                    evidence=[f"name {names}", f"image {image}", f"compose project {proj or '-'}"])
        if state == "running":
            if prov in ("ledger", "attributed"):
                items.append(Item(kind="container.running", level="light" if prov == "ledger" else "standard", cls="S1",
                                  op="docker-stop", args={"id": cid}, undo=f"docker start {cid[:12]}",
                                  reason=f"running container {names} started for this {'session' if prov == 'ledger' else 'project'}",
                                  **base))
            else:
                items.append(Item(kind="container.running-foreign", level="deep", scope="machine", cls="S0", op="report",
                                  reason=f"running container {names} not attributable to this repo", **base))
        else:
            mine = prov in ("ledger", "attributed")
            items.append(Item(kind="container.stopped", level="standard" if mine else "deep",
                              scope="repo" if mine else "machine", cls="S2", op="docker-rm", args={"id": cid},
                              undo="recreate it (e.g. docker compose up); its writable layer is not recoverable",
                              reason=f"{state} container {names}", **base))

    images = _docker_json(["images", "--no-trunc", "--format", "{{json .}}"])
    for im in images:
        repo_, tag, iid = im.get("Repository", ""), im.get("Tag", ""), im.get("ID", "")
        ref = f"{repo_}:{tag}"
        if ref in used_images or repo_ in used_images or iid in used_images:
            continue
        prot = "protected image" if (match_any(ref, pi) or match_any(repo_, pi)) else None
        is_proj = any(repo_ == p or repo_.startswith(p + "-") or repo_.startswith(p + "_") for p in projects)
        dangling = repo_ == "<none>"
        items.append(Item(domain="runtime", kind="image.dangling" if dangling else "image.unused",
                          target=(iid.split(":")[-1][:12]), level="deep", scope="repo" if is_proj else "machine", cls="S2", op="docker-rmi",
                          args={"id": iid}, provenance="attributed" if is_proj else "unknown",
                          size=_size_bytes(im.get("Size", "")), protected=prot, fingerprint={"id": iid},
                          undo=f"docker pull / rebuild {ref}", reason=f"image {ref} not used by any container"))

    for v in _docker_json(["volume", "ls", "--format", "{{json .}}"]):
        name = v.get("Name", "")
        labels = _labels(v.get("Labels", ""))
        proj = labels.get("com.docker.compose.project", "")
        if proj in projects:
            items.append(Item(domain="runtime", kind="volume.project", target=name, level="deep", cls="S3",
                              op="docker-volume-rm", args={"name": name}, provenance="attributed",
                              fingerprint={"name": name}, undo="none: volume data is gone",
                              reason=f"volume of compose project {proj}: may hold a database; confirm by name"))
    dangling_v = run(["docker", "volume", "ls", "-q", "-f", "dangling=true"], timeout=30)[1].split()
    have_v = {i.target for i in items if i.kind == "volume.project"}
    for name in dangling_v:
        if name in have_v:
            continue
        items.append(Item(domain="runtime", kind="volume.dangling", target=name, level="deep", scope="machine", cls="S3",
                          op="docker-volume-rm", args={"name": name}, provenance="unknown",
                          fingerprint={"name": name}, undo="none: volume data is gone",
                          reason="dangling volume (no container references it): confirm by name"))

    for n in _docker_json(["network", "ls", "--format", "{{json .}}"]):
        labels = _labels(n.get("Labels", ""))
        if labels.get("com.docker.compose.project", "") in projects and n.get("Name") not in ("bridge", "host", "none"):
            items.append(Item(domain="runtime", kind="network.project", target=n.get("Name", ""), level="deep", cls="S1",
                              op="docker-network-rm", args={"name": n.get("Name")}, provenance="attributed",
                              fingerprint={"id": n.get("ID")}, undo="docker compose up recreates it",
                              reason="network of this compose project"))

    for row in _docker_json(["system", "df", "--format", "{{json .}}"]):
        if row.get("Type") == "Build Cache" and _size_bytes(row.get("Reclaimable", "")):
            items.append(Item(domain="runtime", kind="docker.build-cache", target="docker build cache", level="deep", scope="machine",
                              cls="S2", op="cmd", args={"argv": ["docker", "builder", "prune", "-f"]},
                              size=_size_bytes(row.get("Reclaimable", "")), provenance="unknown",
                              undo="rebuilt on the next build", reason="reclaimable build cache"))
    return items


def _process_table() -> List[dict]:
    code, out, _ = run(["ps", "-Ao", "pid=,ppid=,uid=,etime=,command="], timeout=20)
    rows = []
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid, ppid, uid, etime, cmd = parts
        try:
            rows.append({"pid": int(pid), "ppid": int(ppid), "uid": int(uid),
                         "elapsed": parse_etime(etime) or 0.0, "cmd": cmd})
        except ValueError:
            continue
    return rows


def _cwds(pids: List[int]) -> Dict[int, str]:
    out: Dict[int, str] = {}
    if not pids:
        return out
    if os.path.isdir("/proc/self"):
        for p in pids:
            try:
                out[p] = os.readlink(f"/proc/{p}/cwd")
            except OSError:
                pass
        return out
    code, text, _ = run(["lsof", "-a", "-d", "cwd", "-p", ",".join(map(str, pids)), "-Fpn"], timeout=30)
    cur = None
    for line in text.splitlines():
        if line.startswith("p"):
            cur = int(line[1:])
        elif line.startswith("n") and cur is not None:
            out[cur] = line[1:]
    return out


def _listening() -> Dict[int, List[str]]:
    code, text, _ = run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-Fpn"], timeout=30)
    ports: Dict[int, List[str]] = {}
    cur = None
    for line in text.splitlines():
        if line.startswith("p"):
            cur = int(line[1:])
        elif line.startswith("n") and cur is not None:
            ports.setdefault(cur, []).append(line[1:])
    return ports


def _short(cmd: str, n: int = 90) -> str:
    """argv0's basename plus the arguments: the part of a command line a reviewer recognises."""
    head, _, rest = cmd.partition(" ")
    return (os.path.basename(head) + (" " + rest if rest else ""))[:n]


def _is_shell(cmd: str) -> bool:
    return os.path.basename(cmd.split()[0]).lstrip("-") in ("sh", "bash", "zsh", "dash", "fish", "nohup", "env")


def _orphaned(pid: int, table: Dict[int, dict]) -> bool:
    """Reparented to init, possibly through a chain of dev processes (a python shim, npm -> node).

    Climbing stops at anything that is not a dev process (a shell, a terminal, an
    editor, Claude Code): a live one of those means somebody still owns the process.
    """
    cur = pid
    for _ in range(12):
        row = table.get(cur)
        if row is None:
            return False
        if row["ppid"] == 1:
            return True
        parent = table.get(row["ppid"])
        if parent is None:
            return False
        detached_shell = _is_shell(parent["cmd"]) and parent["ppid"] == 1
        if not (_is_dev(parent["cmd"]) or detached_shell):
            return False
        cur = row["ppid"]
    return False


def _ancestors(pid: int, table: Dict[int, dict]) -> Set[int]:
    seen: Set[int] = set()
    while pid in table and pid not in seen and pid > 1:
        seen.add(pid)
        pid = table[pid]["ppid"]
    return seen


def collect_processes(root: str, cfg: dict, ledger: dict, notes: List[str], now: Optional[float] = None) -> List[Item]:
    now = now or time.time()
    items: List[Item] = []
    rows = _process_table()
    table = {r["pid"]: r for r in rows}
    me = _ancestors(os.getpid(), table)
    uid = os.getuid()
    cands = [r for r in rows if r["uid"] == uid and r["pid"] not in me and r["cmd"] and _is_dev(r["cmd"])]
    cwds = _cwds([r["pid"] for r in cands])
    ports = _listening()
    rroot = os.path.realpath(root)
    ledger_cmds = ledger.get("process", {})
    for r in cands:
        pid, cmd = r["pid"], r["cmd"]
        cwd = os.path.realpath(cwds.get(pid, "")) if cwds.get(pid) else ""
        inside = bool(cwd) and (cwd == rroot or cwd.startswith(rroot + os.sep))
        started = now - r["elapsed"]
        in_ledger = any(c and c in cmd and started >= float(meta.get("ts", 0)) - 5 for c, meta in ledger_cmds.items())
        orphan = _orphaned(pid, table)
        prov = "ledger" if in_ledger else ("attributed" if inside else "unknown")
        ev = [f"cwd {cwd or '?'}", f"ppid {r['ppid']}" + (" (orphaned)" if orphan else ""),
              f"up {r['elapsed'] / 3600:.1f} h"] + ([f"listening {', '.join(ports[pid])}"] if pid in ports else [])
        base = dict(domain="runtime", target=str(pid), provenance=prov, evidence=ev,
                    age_days=round(r["elapsed"] / 86400, 2),
                    fingerprint={"pid": pid, "started": round(started), "cmd": cmd[:200]},
                    args={"pid": pid}, undo=f"restart it: {cmd[:120]}")
        if prov == "ledger":
            items.append(Item(kind="process.session", level="light", cls="S1", op="kill",
                              reason=f"started by this session: {_short(cmd)}", **base))
        elif inside and orphan:
            items.append(Item(kind="process.orphan", level="standard", cls="S2", op="kill",
                              reason=f"orphaned process running in this repo: {_short(cmd)}", **base))
        elif inside:
            items.append(Item(kind="process.live", level="standard", cls="S0", op="report",
                              reason=f"process in this repo with a live parent (likely someone's terminal): {_short(cmd)}", **base))
        elif orphan:
            items.append(Item(kind="process.orphan-foreign", level="deep", scope="machine", cls="S3", op="kill",
                              reason=f"orphaned dev process outside this repo: {_short(cmd)}", **base))
    return items
