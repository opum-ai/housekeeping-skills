# Branch and worktree cleanup: fixture/repo

**Level: Deep, scope: repo, git domain only.** I picked this level myself: you asked to clean up branches and worktrees and said the repo was "a total mess". I used the git-hygiene skill with the `hk` engine and ran it without GitHub PR checks (`--no-gh`), because this remote is a local bare repo. You said "whatever is safe", so I only applied S1 items: removals the engine proved safe, which can all be undone. Anything that needed your decision is left exactly as it was and listed below.

## What I removed (5 items, all S1)

| Item | Why it was safe (containment proof) |
|---|---|
| worktree `fixture/wt-clean` (branch `feat/wt-clean`) | It had no uncommitted changes, and its branch tip `b5be1e2` is `origin/dev`. I removed it with plain `git worktree remove`, not `--force`. |
| local branch `feat/merged` (`739626f`) | It is an ancestor of `origin/dev`. |
| local branch `feat/squashed` (`bce428d`) | It was squash-merged. `git merge-tree --write-tree origin/dev feat/squashed` gives exactly the tree of `origin/dev` (`9cf1631`), so all of its content is already on dev. |
| local branch `feat/wt-clean` (`b5be1e2`) | It is the same commit as `origin/dev`. |
| remote branch `origin/feat/merged` (`739626f`) | It is an ancestor of `origin/dev`. I deleted it on the remote with a push. |

**Undo:** each change is recorded in a journal, `repo/.git/housekeeping/journal/20260927T091103-deep.jsonl`.
- Undo everything with `python3 .../scripts/hk.py undo <that journal>`.
- Or restore one branch by hand, e.g. `git branch feat/squashed bce428d`.

The saved plan is at `outputs/plan-deep.json`.

## What I left alone: your call

1. **`feat/unlanded` (`42bc917`): unlanded work.** It has one commit that dev doesn't have: "unique work, never merged", which adds `d.txt`. It is not merged, not squash-merged, and has no upstream.
   - Merge it or open a PR if you want it.
   - If you want it gone, archive it first: `git tag archive/feat/unlanded 42bc917 && git branch -D feat/unlanded`.
2. **`feat/gone` (`a7f31a4`): its upstream is gone, but it was never merged.** Its remote branch was deleted, yet its one commit ("pushed then upstream deleted, never merged", which adds `e.txt`) is not on dev. A branch whose upstream is gone is not a landed branch, so I kept it. Decide as for `feat/unlanded`.
3. **`wt-dirty` worktree / `feat/wt-dirty`: an untracked file.** The branch has no commits of its own (it points at `origin/dev`). The worktree, though, holds an untracked `wip.py` that exists nowhere else.
   - If you want it, commit it on a branch.
   - If you don't, delete the file. Then `git worktree remove ../wt-dirty && git branch -d feat/wt-dirty` is safe.
   - I did not remove the worktree, because that would delete `wip.py`.
4. **`retain/perf-experiment` (`47e2c6a`): kept on purpose.** It is unlanded ("experiment kept on purpose"). The `retain/*` prefix marks it as deliberately preserved, so the engine protects it. I didn't touch it.

## Notes (no action taken)

- **`main` is behind `dev`.** `main` is at `dfcfa6d`, and dev has 3 commits on top of it (feature a, feature b, and "dev moves on"). Promotion happens only when you ask for it, so I didn't promote. When you want to, it should be a fast-forward.
- **The main checkout is on `dev`.** It is clean and in sync with `origin/dev`. `hk` flags this only as a reminder: new work belongs on a task branch, not on dev.
- **`hk plan` refreshed the remote-tracking refs.** It ran `git fetch --prune`, which updated them. Nothing else was fetched or changed.
- **No stashes and no stale-unlanded (S3) items** were found, so no confirmations were needed.

## Final state

- **Local branches:** `dev`, `main`, `feat/gone`, `feat/unlanded`, `feat/wt-dirty`, `retain/perf-experiment`.
- **Remote branches:** `origin/dev`, `origin/main`.
- **Worktrees:** `repo` (dev), `wt-dirty` (feat/wt-dirty).
