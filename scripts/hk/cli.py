"""hk command line. Every command supports --json ({schemaVersion, kind, data})."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from . import config as cfgmod
from . import files as filesmod
from . import harness as harnessmod
from . import ledger as ledgermod
from . import plan as planmod
from . import runtime as runtimemod
from .git import Repo, collect as collect_git, status as git_status
from .model import (CLASSES, EXIT_FINDINGS, EXIT_NOT_FOUND, EXIT_OK, EXIT_USAGE, LEVEL_NAMES, LEVELS, SCOPES, Item,
                    envelope, human_size, level_index, normalize_level, scope_index)
from .util import have, run, state_dir, trash_available

DOMAINS = ["git", "files", "tmp", "runtime", "harness", "caches"]
# The lowest level at which a domain can contribute planned items.
DOMAIN_MIN_LEVEL = {"git": "minimal", "files": "minimal", "tmp": "light", "runtime": "light", "harness": "deep",
                    "caches": "deep"}


def _root(path: str) -> str:
    code, out, _ = run(["git", "-C", path, "rev-parse", "--show-toplevel"])
    if code != 0:
        raise SystemExit(_die(f"not a git repository: {path}", EXIT_NOT_FOUND))
    return out.strip()


def _die(msg: str, code: int) -> int:
    print(json.dumps({"error": msg}), file=sys.stderr)
    return code


def gather(root: str, level: str, domains: List[str], fetch: bool, gh: bool, sizes: bool,
           session: Optional[str], scope: str = "repo") -> tuple:
    cfg = cfgmod.load(root)
    led = ledgermod.load(root, session)
    repo = Repo(root, cfg)
    notes: List[str] = []
    items: List[Item] = []
    li = level_index(level)
    machine = scope == "machine"
    want = [d for d in domains if level_index(DOMAIN_MIN_LEVEL[d]) <= li and (d != "caches" or machine)]
    if "git" in want:
        items += collect_git(repo, led, fetch=fetch, use_gh=gh)
    if "files" in want:
        items += filesmod.collect(root, cfg, led, level, sizes=sizes)
    if "tmp" in want:
        items += filesmod.collect_tmp(root, cfg, led, sizes=sizes)
    if "runtime" in want:
        items += runtimemod.collect_docker(root, cfg, led, notes)
        items += runtimemod.collect_processes(root, cfg, led, notes)
    if "harness" in want:
        slugs = filesmod.project_slugs(root)
        items += filesmod.collect_scratchpads(root, cfg, level, sizes=sizes)
        if machine:  # user-wide harness state belongs to machine scope
            items += harnessmod.collect_plugin_cache(sizes=sizes)
            items += harnessmod.collect_projects(sizes=sizes)
        items += harnessmod.collect_context(root, slugs)
        items += harnessmod.collect_settings(root)
        items += harnessmod.collect_duplicate_skills(root)
    if "caches" in want:
        items += harnessmod.collect_caches(sizes=sizes)
    if not trash_available():
        notes.append("no trash tool found: file removals are permanent, so trash items are raised one class")
    return cfg, repo, items, repo.notes + notes


def render_plan(plan: dict) -> str:
    lv = plan["level"]
    lines = [f"# Housekeeping plan: {LEVEL_NAMES[lv]}, {plan.get('scope', 'repo')} scope", ""]
    if plan.get("chosen_by"):
        lines += [f"Level chosen by: {plan['chosen_by']}", ""]
    s = plan["summary"]
    lines.append(f"{s['planned']} planned item(s), {s['findings']} finding(s) for review.")
    lines.append("")
    for cls in CLASSES:
        rows = [i for i in plan["items"] if i["cls"] == cls]
        if not rows:
            continue
        total = sum(i.get("size") or 0 for i in rows)
        gate = {"S0": "no gate", "S1": "reversible: runs without asking",
                "S2": "regenerable: approve once as a batch (--approve-s2)",
                "S3": "IRREVERSIBLE: confirm each by id (--confirm <id>)"}[cls]
        lines += [f"## {cls}: {len(rows)} item(s), {human_size(total)} ({gate})", "",
                  "| id | level | kind | target | size | why |", "|---|---|---|---|---|---|"]
        for i in rows:
            tgt = i["target"]
            if len(tgt) > 70:
                tgt = "…" + tgt[-69:]
            lines.append(f"| `{i['id']}` | {i['level']} | {i['kind']} | `{tgt}` | {human_size(i.get('size'))} | {i['reason']} |")
        lines.append("")
    if plan["findings"]:
        lines += ["## Findings (not planned: review, land, or decide)", ""]
        for i in plan["findings"]:
            prot = f" [protected: {i['protected']}]" if i.get("protected") else ""
            lines.append(f"- `{i['id']}` **{i['kind']}** `{i['target']}`: {i['reason']}{prot}")
        lines.append("")
    if plan.get("notes"):
        lines += ["## Notes", ""] + [f"- {n}" for n in plan["notes"]] + [""]
    return "\n".join(lines)


def _level_scope(a, root: str) -> tuple:
    cfg = cfgmod.load(root)
    level = normalize_level(a.level or cfg.get("housekeeping_level") or "standard")
    scope = (a.scope or cfg.get("housekeeping_scope") or "repo").lower()
    scope_index(scope)
    return level, scope


def cmd_inventory(a) -> int:
    root = _root(a.root)
    level, scope = _level_scope(a, root)
    if not a.level:
        level = "immaculate"  # an inventory shows everything in scope unless narrowed
    cfg, repo, items, notes = gather(root, level, a.domains, not a.no_fetch, not a.no_gh, not a.no_sizes, a.session, scope)
    items = [i for i in items if level_index(i.level) <= level_index(level) and scope_index(i.scope) <= scope_index(scope)]
    if a.json:
        print(envelope("hk.inventory", {"root": root, "level": level, "items": [i.to_dict() for i in items], "notes": notes}))
    else:
        for i in items:
            prot = f" [protected: {i.protected}]" if i.protected else ""
            print(f"{i.id}  {i.level} {i.cls}  {i.kind:<24} {i.target}  {human_size(i.size)}  {i.reason}{prot}")
        for n in notes:
            print(f"note: {n}")
    return EXIT_FINDINGS if any(i.actionable for i in items) else EXIT_OK


def cmd_plan(a) -> int:
    root = _root(a.root)
    level, scope = _level_scope(a, root)
    cfg, repo, items, notes = gather(root, level, a.domains, not a.no_fetch, not a.no_gh, not a.no_sizes, a.session, scope)
    plan = planmod.build_plan(items, level, root, notes, a.chosen_by or "", scope=scope)
    path = planmod.save_plan(plan, root, a.out)
    if a.json:
        print(envelope("hk.plan", {"path": path, **plan}))
    else:
        print(render_plan(plan))
        print(f"Plan saved: {path}")
    return EXIT_FINDINGS if plan["items"] else EXIT_OK


def cmd_apply(a) -> int:
    if not os.path.exists(a.plan):
        return _die(f"plan not found: {a.plan}", EXIT_NOT_FOUND)
    plan = planmod.load_plan(a.plan)
    root = plan["root"]
    cfg = cfgmod.load(root)
    repo = Repo(root, cfg)
    only = [x for x in (a.only or "").split(",") if x]
    confirm = [x for x in (a.confirm or "").split(",") if x]
    summary, code = planmod.apply(plan, repo, cfg, only=only, approve_s2=a.approve_s2, confirm=confirm,
                                  dry_run=a.dry_run, force_kill=a.force_kill)
    if a.json:
        print(envelope("hk.apply", summary))
    else:
        for r in summary["results"]:
            print(f"{r['result']:<12} {r['id']}  {r['op']:<22} {r['target']}  {r.get('detail', '')}")
        print(f"counts: {summary['counts']}  reclaimed: {human_size(summary['reclaimed_bytes'])}")
        if summary["journal"]:
            print(f"journal: {summary['journal']}  (undo: hk undo {summary['journal']})")
    return code


def cmd_undo(a) -> int:
    if not os.path.exists(a.journal):
        return _die(f"journal not found: {a.journal}", EXIT_NOT_FOUND)
    out, code = planmod.undo(a.journal, [x for x in (a.only or "").split(",") if x])
    print(envelope("hk.undo", out) if a.json else "\n".join(f"{'undone' if o['undone'] else 'MANUAL':<8} {o['id']}  {o['detail']}" for o in out))
    return code


def _quest_state(root: str) -> dict:
    if not have("quest") or not os.path.isdir(os.path.join(root, ".quest")):
        return {"available": False}
    code, out, _ = run(["quest", "task", "list", "--status", "In Progress", "--json"], cwd=root)
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"available": True, "error": f"exit {code}"}
    rows = data.get("data")
    tasks = rows if isinstance(rows, list) else (rows or {}).get("tasks", [])
    return {"available": True, "in_progress": [{"id": t.get("id"), "title": t.get("title")} for t in tasks],
            "scope": data.get("scope") or (rows or {}).get("scope") if isinstance(rows, dict) else data.get("scope")}


def _lore_state(root: str) -> dict:
    if not have("lore") or not os.path.isdir(os.path.join(root, ".lore")):
        return {"available": False}
    code, _, _ = run(["lore", "check", "--json"], cwd=root, timeout=120)
    return {"available": True, "check_exit": code}


def _open_prs(root: str) -> dict:
    if not have("gh"):
        return {"available": False}
    code, out, _ = run(["gh", "pr", "list", "--state", "open", "--json", "number,headRefName,title"], cwd=root)
    if code != 0:
        return {"available": False}
    return {"available": True, "open": json.loads(out or "[]")}


def cmd_status(a) -> int:
    root = _root(a.root)
    cfg = cfgmod.load(root)
    repo = Repo(root, cfg)
    data = {"git": git_status(repo), "quest": _quest_state(root), "lore": _lore_state(root),
            "prs": _open_prs(root) if not a.no_gh else {"available": False}}
    if a.json:
        print(envelope("hk.status", data))
    else:
        g = data["git"]
        print(f"branch {g['branch']} (trunk {g['trunk']}, release {g['release']}), upstream {g['upstream']}, "
              f"ahead {g['ahead']}, uncommitted {g['uncommitted']}")
        for f in g["findings"]:
            print(f"finding: {f}")
        q = data["quest"]
        if q.get("available"):
            print(f"quest In Progress: {[t['id'] for t in q.get('in_progress', [])]}  scope={q.get('scope')}")
        if data["lore"].get("available"):
            print(f"lore check exit {data['lore']['check_exit']}")
        if data["prs"].get("available"):
            print(f"open PRs: {[p['number'] for p in data['prs']['open']]}")
    return EXIT_OK


def cmd_ledger(a) -> int:
    root = _root(a.root)
    if a.ledger_cmd == "add":
        e = ledgermod.add(root, a.kind, a.target, session=a.session, cmd=a.cmd)
        print(envelope("hk.ledger.added", e) if a.json else f"recorded {e['kind']} {e['target']}")
        return EXIT_OK
    data = ledgermod.load(root, a.session)
    print(envelope("hk.ledger", data) if a.json else "\n".join(f"{k}: {len(v)}" for k, v in data.items()))
    return EXIT_OK


DISPOSITIONS = ("kept", "removed", "landed", "deferred", "accepted")


def cmd_disposition(a) -> int:
    """Immaculate's check: every in-scope item has an intentional disposition.

    Protected and keep-list items are auto-disposed as kept (with the reason). Everything
    else needs one recorded with --set <id>=<kept|removed|landed|deferred|accepted>:<reason>.
    Exit 0 when nothing is unaccounted for, 6 otherwise.
    """
    root = _root(a.root)
    level, scope = _level_scope(a, root)
    path = os.path.join(state_dir(root), "dispositions.json")
    try:
        recorded = json.load(open(path))
    except (OSError, json.JSONDecodeError):
        recorded = {}
    for spec in a.set or []:
        iid, _, rest = spec.partition("=")
        kind, _, reason = rest.partition(":")
        if kind not in DISPOSITIONS or not reason.strip():
            return _die(f"--set needs <id>=<{'|'.join(DISPOSITIONS)}>:<reason>, got {spec!r}", EXIT_USAGE)
        recorded[iid] = {"disposition": kind, "reason": reason.strip()}
    with open(path, "w") as fh:
        json.dump(recorded, fh, indent=2)
    cfg, repo, items, notes = gather(root, level, a.domains, not a.no_fetch, not a.no_gh, not a.no_sizes, a.session, scope)
    rows = []
    for i in items:
        if level_index(i.level) > level_index(level) or scope_index(i.scope) > scope_index(scope):
            continue
        d = recorded.get(i.id)
        if d is None and i.protected:
            d = {"disposition": "kept", "reason": f"protected: {i.protected}"}
        rows.append({"id": i.id, "kind": i.kind, "target": i.target, "class": i.cls, "reason": i.reason,
                     "disposition": d})
    open_rows = [r for r in rows if not r["disposition"]]
    data = {"level": level, "scope": scope, "items": rows, "unaccounted": len(open_rows), "notes": notes,
            "record": path}
    if a.json:
        print(envelope("hk.disposition", data))
    else:
        for r in rows:
            d = r["disposition"]
            tag = f"{d['disposition']}: {d['reason']}" if d else "UNACCOUNTED"
            print(f"{r['id']}  {r['kind']:<24} {r['target']}  -> {tag}")
        print(f"{len(open_rows)} unaccounted of {len(rows)} (record: {path})")
    return EXIT_FINDINGS if open_rows else EXIT_OK


def cmd_doctor(a) -> int:
    tools = {t: have(t) for t in ("git", "gh", "docker", "quest", "lore", "claude", "lsof")}
    data = {"python": sys.version.split()[0], "tools": tools, "trash": trash_available(),
            "git_merge_tree": run(["git", "merge-tree", "-h"])[0] in (0, 129) and "write-tree" in run(["git", "merge-tree", "-h"])[1] + run(["git", "merge-tree", "-h"])[2]}
    print(envelope("hk.doctor", data) if a.json else "\n".join(f"{k}: {v}" for k, v in data.items()))
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="hk", description="Housekeeping engine: inventory, plan, apply, undo.")
    p.add_argument("--root", default=".", help="path inside the repository (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--level", help=f"{' | '.join(LEVELS)} (or 1-5); default: housekeeping_level from config")
        sp.add_argument("--scope", choices=SCOPES, help="default: housekeeping_scope from config (repo)")
        sp.add_argument("--domains", default=",".join(DOMAINS), type=lambda s: [d for d in s.split(",") if d])
        sp.add_argument("--no-fetch", action="store_true", help="skip git fetch --prune (proofs may use stale refs)")
        sp.add_argument("--no-gh", action="store_true", help="skip GitHub PR-state proofs")
        sp.add_argument("--no-sizes", action="store_true", help="skip du (faster)")
        sp.add_argument("--session", help="restrict ledger provenance to one session id")
        sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("inventory", help="everything found up to a level (read-only)")
    common(sp)
    sp.set_defaults(fn=cmd_inventory)
    sp = sub.add_parser("plan", help="write a reviewable plan for a level (read-only)")
    common(sp)
    sp.add_argument("--out")
    sp.add_argument("--chosen-by", help="how the level was chosen, for the report")
    sp.set_defaults(fn=cmd_plan)
    sp = sub.add_parser("apply", help="execute exactly a saved plan")
    sp.add_argument("plan")
    sp.add_argument("--only", help="comma-separated item ids")
    sp.add_argument("--approve-s2", action="store_true", help="the user approved the S2 batch")
    sp.add_argument("--confirm", help="comma-separated S3 item ids the user confirmed by name")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--force-kill", action="store_true", help="SIGKILL processes that ignore SIGTERM")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_apply)
    sp = sub.add_parser("undo", help="reverse applied items from a journal where possible")
    sp.add_argument("journal")
    sp.add_argument("--only")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_undo)
    sp = sub.add_parser("status", help="landing state: git, quest, lore, PRs (read-only)")
    sp.add_argument("--no-gh", action="store_true")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_status)
    sp = sub.add_parser("ledger", help="provenance ledger")
    lsub = sp.add_subparsers(dest="ledger_cmd", required=True)
    la = lsub.add_parser("add")
    la.add_argument("--kind", required=True, choices=list(ledgermod.KINDS))
    la.add_argument("--target", required=True)
    la.add_argument("--cmd")
    la.add_argument("--session")
    la.add_argument("--json", action="store_true")
    ls = lsub.add_parser("show")
    ls.add_argument("--session")
    ls.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_ledger)
    sp = sub.add_parser("disposition", help="Immaculate: list every in-scope item and its recorded disposition")
    common(sp)
    sp.add_argument("--set", action="append", help="<id>=<kept|removed|landed|deferred|accepted>:<reason>")
    sp.set_defaults(fn=cmd_disposition)
    sp = sub.add_parser("doctor", help="which tools the engine can use here")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_doctor)

    a = p.parse_args(argv)
    if getattr(a, "level", None):
        try:
            a.level = normalize_level(a.level)
        except ValueError as e:
            return _die(str(e), EXIT_USAGE)
    a.root = os.path.abspath(a.root)
    try:
        return a.fn(a)
    except SystemExit as e:
        return int(e.code or 0)
