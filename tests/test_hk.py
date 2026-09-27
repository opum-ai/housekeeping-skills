import json
import os
import subprocess
import sys

from conftest import HK, commit, git

from hk import config as cfgmod
from hk import files as filesmod
from hk import ledger as ledgermod
from hk import plan as planmod
from hk.git import Repo, collect
from hk.model import Item, raise_class


def by_target(items):
    return {i.target: i for i in items}


def git_items(root):
    repo = Repo(root, cfgmod.load(root))
    return repo, collect(repo, ledgermod.load(root), fetch=True, use_gh=False)


# --- R-5: a branch with unique commits is unlanded work, not clutter ----------

def test_branch_classification_never_plans_unlanded_work(estate):
    repo, items = git_items(estate["root"])
    t = by_target(items)
    assert t["refs/heads/feat/merged"].kind == "branch.landed"
    assert "ancestor" in t["refs/heads/feat/merged"].reason
    assert t["refs/heads/feat/squashed"].kind == "branch.landed"
    assert "merge-tree" in t["refs/heads/feat/squashed"].reason
    for name in ("feat/unlanded", "feat/gone"):
        it = t[f"refs/heads/{name}"]
        assert it.kind == "branch.unlanded" and it.op == "report" and not it.actionable, name
    assert any("upstream deleted" in e for e in t["refs/heads/feat/gone"].evidence)
    assert not t["refs/heads/retain/experiment"].actionable
    assert t["refs/heads/feat/in-worktree"].protected.startswith("checked out in worktree")
    assert "refs/heads/dev" not in t and "refs/heads/main" not in t


def test_plan_contains_only_landed_branches_and_no_dirty_worktree(estate):
    repo, items = git_items(estate["root"])
    plan = planmod.build_plan(items, "C5", estate["root"], [])
    planned = {i["target"] for i in plan["items"]}
    assert "refs/heads/feat/merged" in planned and "refs/heads/feat/squashed" in planned
    assert "refs/remotes/origin/feat/merged" in planned
    for keep in ("feat/unlanded", "feat/gone", "retain/experiment", "feat/in-worktree"):
        assert f"refs/heads/{keep}" not in planned
    assert estate["wt"] not in planned  # dirty worktree is a finding, never a removal
    assert any(f["kind"] == "worktree.dirty" for f in plan["findings"])


def test_stale_unlanded_branch_is_s3_and_archived_before_delete(estate):
    root = estate["root"]
    with open(os.path.join(root, ".housekeeping.toml"), "w") as fh:
        fh.write("[branches]\nstale_days = 0\n")
    repo, items = git_items(root)
    it = by_target(items)["refs/heads/feat/unlanded"]
    assert it.kind == "branch.stale-unlanded" and it.cls == "S3" and it.level == "C4"
    plan = planmod.build_plan(items, "C4", root, [])
    summary, _ = planmod.apply(plan, repo, cfgmod.load(root), approve_s2=True)
    rec = next(r for r in summary["results"] if r["id"] == it.id)
    assert rec["result"] == "gated"  # S3 never runs on batch approval
    summary, _ = planmod.apply(plan, repo, cfgmod.load(root), only=[it.id], confirm=[it.id])
    assert summary["results"][0]["result"] == "applied"
    tip = it.fingerprint["tip"]
    assert git(root, "rev-parse", "refs/tags/archive/feat/unlanded") == tip


def test_apply_deletes_landed_branches_and_undo_restores(estate):
    root = estate["root"]
    repo, items = git_items(root)
    plan = planmod.build_plan(items, "C3", root, [])
    summary, code = planmod.apply(plan, repo, cfgmod.load(root), approve_s2=True)
    assert code == 0
    heads = git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads").split()
    assert "feat/merged" not in heads and "feat/squashed" not in heads
    assert {"feat/unlanded", "feat/gone", "retain/experiment", "feat/in-worktree"} <= set(heads)
    remote_heads = git(estate["remote"], "for-each-ref", "--format=%(refname:short)", "refs/heads").split()
    assert "feat/merged" not in remote_heads
    out, code = planmod.undo(summary["journal"])
    assert code == 0
    heads = git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads").split()
    assert "feat/merged" in heads and "feat/squashed" in heads


def test_branch_that_moved_after_planning_is_skipped(estate):
    root = estate["root"]
    repo, items = git_items(root)
    plan = planmod.build_plan(items, "C3", root, [])
    git(root, "checkout", "-q", "feat/merged")
    commit(root, "late.txt", "new work\n", "work added after the plan")
    git(root, "checkout", "-q", "dev")
    summary, code = planmod.apply(plan, repo, cfgmod.load(root))
    rec = next(r for r in summary["results"] if r["target"] == "refs/heads/feat/merged")
    assert rec["result"] == "drift" and code == 5
    assert "feat/merged" in git(root, "branch", "--list", "feat/merged")


# --- files: trash by default, never protected or tracked paths ---------------

def make_files(root):
    with open(os.path.join(root, ".gitignore"), "w") as fh:
        fh.write("node_modules/\n.env\n*.log\n.idea/\n")
    git(root, "add", ".gitignore")
    git(root, "commit", "-q", "-m", "ignore")
    os.makedirs(os.path.join(root, "node_modules", "left-pad"))
    open(os.path.join(root, "node_modules", "left-pad", "index.js"), "w").write("x")
    open(os.path.join(root, ".env"), "w").write("SECRET=1\n")
    open(os.path.join(root, "notes.bak"), "w").write("junk\n")
    open(os.path.join(root, "server.log"), "w").write("log\n")
    open(os.path.join(root, "new_module.py"), "w").write("real work\n")
    os.makedirs(os.path.join(root, ".idea"))
    open(os.path.join(root, ".idea", "workspace.xml"), "w").write("<x/>")
    commit(root, "tracked.bak", "tracked on purpose\n", "a tracked file with a junk name")


def test_file_classification(estate):
    root = estate["root"]
    make_files(root)
    items = by_target(filesmod.collect(root, cfgmod.load(root), ledgermod.load(root), "C5", sizes=False))
    j = items[os.path.join(root, "notes.bak")]
    assert j.kind == "file.junk" and j.level == "C2" and j.cls == "S2"  # unknown provenance raises S1 -> S2
    assert items[os.path.join(root, "node_modules")].kind == "dir.build"
    assert items[os.path.join(root, "node_modules")].cls == "S2"
    env = items[os.path.join(root, ".env")]
    assert env.protected and not env.actionable
    assert items[os.path.join(root, "new_module.py")].cls == "S3"
    assert items[os.path.join(root, ".idea")].kind == "file.ignored-other"
    assert os.path.join(root, "tracked.bak") not in items


def test_ledger_provenance_lowers_nothing_but_skips_the_raise(estate):
    root = estate["root"]
    make_files(root)
    ledgermod.add(root, "file", "notes.bak", session="s1")
    items = by_target(filesmod.collect(root, cfgmod.load(root), ledgermod.load(root), "C2", sizes=False))
    it = items[os.path.join(root, "notes.bak")]
    assert it.provenance == "ledger" and it.cls == "S1"


def test_apply_trashes_files_and_refuses_protected_and_outside_paths(estate, tmp_path):
    root = estate["root"]
    make_files(root)
    cfg = cfgmod.load(root)
    items = filesmod.collect(root, cfg, ledgermod.load(root), "C4", sizes=False)
    # Forge dangerous items the collectors would never produce; apply must still refuse them.
    outside = tmp_path / "outside.txt"
    outside.write_text("not yours\n")
    forged = [
        Item(domain="files", kind="file.junk", target=str(outside), level="C2", cls="S1", op="trash", reason="forged",
             fingerprint={}),
        Item(domain="files", kind="file.junk", target=os.path.join(root, ".env"), level="C2", cls="S1", op="trash",
             reason="forged", fingerprint={}),
        Item(domain="files", kind="file.junk", target=os.path.join(root, "tracked.bak"), level="C2", cls="S1",
             op="trash", reason="forged", fingerprint={}),
    ]
    plan = planmod.build_plan(items + forged, "C4", root, [])
    repo = Repo(root, cfg)
    summary, code = planmod.apply(plan, repo, cfg, approve_s2=True)
    res = {r["target"]: r for r in summary["results"]}
    assert res[str(outside)]["result"] == "refused" and outside.exists()
    assert res[os.path.join(root, ".env")]["result"] == "refused" and os.path.exists(os.path.join(root, ".env"))
    assert res[os.path.join(root, "tracked.bak")]["result"] == "refused"
    assert res[os.path.join(root, "notes.bak")]["result"] == "applied"
    assert not os.path.exists(os.path.join(root, "notes.bak"))
    trashed = os.listdir(os.environ["HK_TRASH_DIR"])
    assert trashed  # moved, not deleted
    assert not os.path.exists(os.path.join(root, "node_modules"))
    assert os.path.exists(os.path.join(root, "new_module.py"))  # S3 at C5 only, and never at C4


def test_file_changed_after_plan_is_skipped(estate):
    root = estate["root"]
    make_files(root)
    cfg = cfgmod.load(root)
    plan = planmod.build_plan(filesmod.collect(root, cfg, ledgermod.load(root), "C2", sizes=False), "C2", root, [])
    with open(os.path.join(root, "notes.bak"), "a") as fh:
        fh.write("the user edited this after the plan\n")
    summary, code = planmod.apply(plan, Repo(root, cfg), cfg, approve_s2=True)
    rec = next(r for r in summary["results"] if r["target"].endswith("notes.bak"))
    assert rec["result"] == "drift" and os.path.exists(os.path.join(root, "notes.bak"))


def test_s2_needs_batch_approval(estate):
    root = estate["root"]
    make_files(root)
    cfg = cfgmod.load(root)
    plan = planmod.build_plan(filesmod.collect(root, cfg, ledgermod.load(root), "C4", sizes=False), "C4", root, [])
    summary, _ = planmod.apply(plan, Repo(root, cfg), cfg)
    assert all(r["result"] == "gated" for r in summary["results"] if r["cls"] == "S2")
    assert os.path.exists(os.path.join(root, "node_modules"))


# --- stashes -----------------------------------------------------------------

def test_old_stash_is_archived_then_dropped_and_undo_restores(estate):
    root = estate["root"]
    with open(os.path.join(root, ".housekeeping.toml"), "w") as fh:
        fh.write("[stash]\nmax_age_days = 0\n")
    with open(os.path.join(root, "README.md"), "a") as fh:
        fh.write("stashed edit\n")
    git(root, "stash", "push", "-q", "-m", "old idea")
    repo, items = git_items(root)
    st = next(i for i in items if i.kind == "stash.old")
    assert st.cls == "S1" and st.level == "C4"
    plan = planmod.build_plan([st], "C4", root, [])
    summary, code = planmod.apply(plan, repo, cfgmod.load(root))
    assert code == 0 and git(root, "stash", "list") == ""
    sha = st.fingerprint["sha"]
    assert git(root, "rev-parse", f"refs/archive/stash/{sha}") == sha
    planmod.undo(summary["journal"])
    assert "old idea" in git(root, "stash", "list")


# --- config and CLI contract --------------------------------------------------

def test_mini_toml_matches_the_documented_subset():
    text = """
version = 1
[levels]
default = "C3"  # comment
[protect]
containers = ["runner", "db"]
branches = [
  "keep/*",
]
[provenance]
enabled = true
[tmp]
max_age_days = 2.5
"""
    d = cfgmod.mini_toml(text)
    assert d["levels"]["default"] == "C3"
    assert d["protect"]["containers"] == ["runner", "db"]
    assert d["protect"]["branches"] == ["keep/*"]
    assert d["provenance"]["enabled"] is True and d["tmp"]["max_age_days"] == 2.5


def test_config_lists_extend_but_never_replace_builtins(estate):
    root = estate["root"]
    with open(os.path.join(root, ".housekeeping.toml"), "w") as fh:
        fh.write('[protect]\ncontainers = ["my-db"]\n')
    cfg = cfgmod.load(root)
    assert "opum-runner" in cfg["protect"]["containers"] and "my-db" in cfg["protect"]["containers"]


def test_cli_envelope_and_exit_codes(estate):
    root = estate["root"]
    p = subprocess.run([sys.executable, HK, "--root", root, "plan", "--level", "C3", "--no-gh", "--no-sizes",
                        "--domains", "git,files", "--json"], capture_output=True, text=True)
    doc = json.loads(p.stdout)
    assert doc["schemaVersion"] == 1 and doc["kind"] == "hk.plan"
    assert p.returncode == 6  # findings/planned items present
    p2 = subprocess.run([sys.executable, HK, "apply", "/nonexistent/plan.json"], capture_output=True, text=True)
    assert p2.returncode == 3


def test_raise_class_caps_at_s3():
    assert raise_class("S1") == "S2" and raise_class("S3") == "S3"


# --- runtime: only processes attributable to the repo --------------------------

def test_orphaned_dev_server_in_repo_is_found_and_stopped(estate):
    import time as _t

    from hk import runtime

    root = estate["root"]
    marker = f"hk-test-{os.getpid()}"
    # Double-fork so the server is reparented (PPID 1): the orphan shape agents leave behind.
    subprocess.run(["sh", "-c", f"cd '{root}' && nohup {sys.executable} -m http.server 0 --bind 127.0.0.1 "
                    f"--directory . >/dev/null 2>&1 & echo {marker} >/dev/null"], check=True)
    try:
        found = None
        for _ in range(50):
            items = runtime.collect_processes(root, cfgmod.load(root), ledgermod.load(root), [])
            found = next((i for i in items if "http.server" in i.fingerprint.get("cmd", "")), None)
            if found:
                break
            _t.sleep(0.1)
        assert found is not None, "orphaned server in the repo was not found"
        assert found.kind == "process.orphan" and found.provenance == "attributed" and found.level == "C3"
        plan = planmod.build_plan([found], "C3", root, [])
        summary, code = planmod.apply(plan, Repo(root, cfgmod.load(root)), cfgmod.load(root), approve_s2=True)
        assert summary["results"][0]["result"] == "applied", summary
    finally:
        subprocess.run(["pkill", "-f", f"http.server 0 --bind 127.0.0.1 --directory ."], check=False)
