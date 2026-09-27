import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "capture.py")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from hk import ledger as ledgermod  # noqa: E402


def run_hook(payload, raw=None):
    data = raw if raw is not None else json.dumps(payload)
    return subprocess.run([sys.executable, HOOK], input=data, capture_output=True, text=True, timeout=10)


def enable(root):
    with open(os.path.join(root, ".housekeeping.toml"), "w") as fh:
        fh.write("[provenance]\nenabled = true\n")


def test_malformed_input_exits_zero_silently():
    p = run_hook(None, raw="{not json")
    assert p.returncode == 0 and p.stdout == "" and p.stderr == ""


def test_noop_without_config(estate):
    root = estate["root"]
    p = run_hook({"cwd": root, "hook_event_name": "PreToolUse", "tool_name": "Write",
                  "tool_input": {"file_path": os.path.join(root, "x.py")}, "session_id": "s"})
    assert p.returncode == 0
    assert not os.path.exists(os.path.join(root, ".git", "housekeeping", "ledger"))
    assert not os.path.exists(os.path.join(root, ".claude"))


def test_records_new_file_branch_worktree_and_background(estate):
    root = estate["root"]
    enable(root)
    base = {"cwd": root, "session_id": "s1"}
    run_hook({**base, "hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "scratch.py"}})
    run_hook({**base, "hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "README.md"}})
    run_hook({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash",
              "tool_input": {"command": "git worktree add -b feat/x ../wt-x && git checkout -b feat/y"}})
    run_hook({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash",
              "tool_input": {"command": "npm run dev", "run_in_background": True}})
    led = ledgermod.load(root)
    assert os.path.join(root, "scratch.py") in led["file"]
    assert os.path.join(root, "README.md") not in led["file"]  # existed already: not created by the session
    assert {"feat/x", "feat/y"} <= set(led["branch"])
    assert os.path.normpath(os.path.join(root, "..", "wt-x")) in led["worktree"]
    assert "npm run dev" in led["process"]


def test_unwritable_ledger_still_exits_zero(estate):
    root = estate["root"]
    enable(root)
    with open(os.path.join(root, ".git", "housekeeping"), "w") as fh:
        fh.write("a file where the ledger dir should be")
    p = run_hook({"cwd": root, "hook_event_name": "PreToolUse", "tool_name": "Write",
                  "tool_input": {"file_path": "new.py"}, "session_id": "s"})
    assert p.returncode == 0 and p.stderr == ""
