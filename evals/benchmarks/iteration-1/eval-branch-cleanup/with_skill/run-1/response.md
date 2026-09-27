# Branch and worktree cleanup: summary

I used the git-hygiene skill with the `hk` engine (`plan --level C3 --domains git --no-gh`, then `apply`). The rule I followed: a branch is deleted only when there's proof it already landed in `dev`. I checked each proof myself with `git merge-base --is-ancestor` and `git merge-tree` before applying anything. Nothing with unique commits or uncommitted work was deleted.

## What I cleaned up (all reversible)

| Item | Why it was safe |
|---|---|
| local `feat/merged` | Its tip is already part of `origin/dev`'s history |
| local `feat/squashed` | It was squash-merged: merging it into `origin/dev` changes nothing (the result equals dev's tree) |
| remote `origin/feat/merged` (deleted on `origin`) | Its tip is already part of `origin/dev`'s history |
| worktree `../wt-clean` | Clean worktree of a landed branch, removed without `--force` |
| local `feat/wt-clean` | Its tip is already part of `origin/dev`'s history (deleted on a second pass, once its worktree was gone) |

Each action is recorded in a journal, together with the command that reverses it:
- `repo/.claude/housekeeping/journal/20260926T224737-C3.jsonl`
- `repo/.claude/housekeeping/journal/20260926T224747-C3.jsonl`

To reverse them, run `python3 <plugin>/scripts/hk.py undo <journal>`. To bring back a single branch, run `git branch <name> <sha>`. The SHAs were: `feat/merged` 08bbf47, `feat/squashed` 61bc0e2, `feat/wt-clean` e29f042.

## What I left for you (not sure, or not safe to do without you)

1. **`feat/gone` (1832509, 1 unique commit, adds `e.txt`).** Its branch on the remote was deleted, but the commit never landed in `dev`. A deleted remote branch doesn't prove the work was merged. This commit may now exist only on your machine. Choose one:
   - land it with a PR to `dev`, or
   - archive and drop it: `git tag archive/feat/gone feat/gone && git branch -D feat/gone`.
2. **`feat/unlanded` (158b197, 1 unique commit, adds `d.txt`).** This is unmerged work. Land it or drop it, as in item 1.
3. **Worktree `../wt-dirty` on `feat/wt-dirty`.** It has an untracked file, `wip.py`, whose content is `# an uncommitted bug fix that exists nowhere else`. I didn't touch it. Commit it and land it, and then the worktree and branch can be pruned. The branch itself has no commits of its own: it sits at dev's tip.
4. **`retain/perf-experiment` (85326c4, adds `f.txt`).** I kept this on purpose because `retain/*` is the reserved prefix for work you've chosen to keep. Nothing to do unless you no longer want it.

## Other notes

- `dev` is 3 commits ahead of `main`: feature a, feature b (squashed), and "dev moves on". Promoting `dev` to `main` happens only when you ask, so I didn't do it. When you want it, use a fast-forward only.
- The repo is checked out on `dev`. `hk status` flags that new commits belong on a task branch, not on `dev`. The working tree is clean, so nothing needs to happen now.
- `hk` saves its plans and journals under `repo/.claude/housekeeping/`, which shows up as an untracked `.claude/` folder. Keep it so the undo is still possible. Consider adding it to `.gitignore`.
- There were no stashes. I skipped the GitHub PR-state check (`--no-gh`) because `origin` is a local bare repo. The deletions didn't need it: each was proven from git history alone.
