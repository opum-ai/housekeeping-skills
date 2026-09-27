import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

HK = os.path.join(os.path.dirname(__file__), "..", "scripts", "hk.py")


def sh(cwd, *args, check=True):
    p = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"{args} failed: {p.stderr}")
    return p.stdout.strip()


def git(cwd, *args, check=True):
    return sh(cwd, "git", *args, check=check)


def commit(cwd, path, content, msg):
    full = os.path.join(cwd, path)
    os.makedirs(os.path.dirname(full) or cwd, exist_ok=True)
    with open(full, "w") as fh:
        fh.write(content)
    git(cwd, "add", path)
    git(cwd, "commit", "-q", "-m", msg)
    return git(cwd, "rev-parse", "HEAD")


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HK_TRASH_DIR", str(tmp_path / "trash"))
    monkeypatch.setenv("HK_CLAUDE_HOME", str(tmp_path / "claude-home"))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "t")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "t@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "t")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "t@example.com")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)


@pytest.fixture
def estate(tmp_path):
    """A clone of a bare remote with dev as trunk and branches in every containment state."""
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    sh(tmp_path, "git", "init", "-q", "--bare", "-b", "main", str(remote))
    sh(tmp_path, "git", "clone", "-q", str(remote), str(work))
    w = str(work)
    git(w, "checkout", "-q", "-b", "main")
    commit(w, "README.md", "hello\n", "init")
    git(w, "push", "-q", "-u", "origin", "main")
    git(w, "checkout", "-q", "-b", "dev")
    git(w, "push", "-q", "-u", "origin", "dev")

    # merged: fast-forwarded into dev
    git(w, "checkout", "-q", "-b", "feat/merged", "dev")
    commit(w, "a.txt", "a\n", "a")
    git(w, "checkout", "-q", "dev")
    git(w, "merge", "-q", "--ff-only", "feat/merged")

    # squashed: its content landed on dev as a different commit
    git(w, "checkout", "-q", "-b", "feat/squashed", "dev")
    commit(w, "b.txt", "b1\n", "b1")
    commit(w, "b.txt", "b2\n", "b2")
    git(w, "checkout", "-q", "dev")
    git(w, "merge", "-q", "--squash", "feat/squashed")
    git(w, "commit", "-q", "-m", "squash b")
    commit(w, "c.txt", "later\n", "dev moves on")  # dev moves past the squash
    git(w, "push", "-q", "origin", "dev")

    # unlanded: unique work never merged
    git(w, "checkout", "-q", "-b", "feat/unlanded", "dev")
    commit(w, "d.txt", "precious\n", "unique work")

    # gone: pushed, upstream deleted, but its commits never landed
    git(w, "checkout", "-q", "-b", "feat/gone", "dev")
    commit(w, "e.txt", "also precious\n", "gone but unmerged")
    git(w, "push", "-q", "-u", "origin", "feat/gone")
    git(w, "push", "-q", "origin", "--delete", "feat/gone")

    # retain: reserved prefix, landed or not it stays
    git(w, "checkout", "-q", "-b", "retain/experiment", "dev")
    commit(w, "f.txt", "kept on purpose\n", "retain")

    # worktree: a landed branch checked out in a dirty worktree
    git(w, "checkout", "-q", "dev")
    git(w, "branch", "feat/in-worktree", "dev")
    wt = str(tmp_path / "wt")
    git(w, "worktree", "add", "-q", wt, "feat/in-worktree")
    with open(os.path.join(wt, "wip.txt"), "w") as fh:
        fh.write("uncommitted fix\n")

    # remote landed branch that still exists on the remote
    git(w, "push", "-q", "origin", "feat/merged")
    git(w, "fetch", "-q", "--prune")
    return {"root": w, "remote": str(remote), "wt": wt, "tmp": tmp_path}
