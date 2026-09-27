# Branch prune: squash-merged estate

Repo: `fixture/repo` (trunk `dev`, release `main`, remote `origin`). I used the git-hygiene skill with the `hk` engine at the Standard level, git domain only. I ran `git fetch --prune` first. There is no GitHub remote, so the PR-state proof was skipped (`--no-gh`).

## Deleted: 8 local branches, each proven landed

| Branch | Tip | Proof |
|---|---|---|
| feat/T-10-change-0 | f325d96 | content already in origin/dev (merge-tree == origin/dev tree); squash commit `T-10: change 0 (#100)` |
| feat/T-11-change-1 | d40de05 | same; `T-11: change 1 (#101)` |
| feat/T-12-change-2 | a339253 | same; `T-12: change 2 (#102)` |
| feat/T-13-change-3 | 2f4a3cd | same; `T-13: change 3 (#103)` |
| feat/T-14-change-4 | 4f3e6b3 | same; `T-14: change 4 (#104)` |
| feat/T-15-change-5 | 2b8f7db | same; `T-15: change 5 (#105)` |
| feat/T-16-change-6 | a9b251d | same; `T-16: change 6 (#106)` |
| feat/T-17-change-7 | 4c84bc5 | same; `T-17: change 7 (#107)` |

Each of these branches still showed 2 "unique" commits, because the tip of a squash-merged branch never becomes an ancestor of dev. I did not rely on that count or on the `[gone]` upstream. I relied on content equivalence: merging each branch into `origin/dev` gives exactly `origin/dev`'s tree. I checked this independently, outside the engine, and got the same result. Their remote branches had already been deleted.

**Undo** (every deletion is journalled with its SHA):
`python3 scripts/hk.py undo repo/.git/housekeeping/journal/20260927T091058-standard.jsonl`
You can also restore one branch with `git branch <name> <sha>`, using the SHAs above.

## Not touched: needs your decision

1. **`feat/T-30-partial` (5dce7bf), local and `origin/feat/T-30-partial`: UNLANDED.**
   Only half of this work landed (`b466d6a partial: landed half` added `p1.txt`). The other commit, `5dce7bf partial: the half that never landed`, adds `p2.txt` ("UNLANDED part"), and that is not in dev. This is real work, not clutter. Either land it (open a PR into dev) or tell me it is dropped. The remote copy may belong to someone else, so I left both.
2. **`old/2025-spike-do-not-need` (0d0efd0): UNLANDED, idle about 330 days.**
   It has 1 unique commit, `spike nobody merged`, which adds `spike.txt` ("the only copy of a spike"). No other copy exists: it has no remote. The branch name says it isn't needed, but a name is not proof, and deleting it is irreversible. The engine lists it as a Deep S3 item that needs confirmation per item. If you want it gone, the safe path archives it to `refs/tags/archive/old/2025-spike-do-not-need` before deleting:
   `hk plan --level deep --domains git`, then `hk apply <plan> --confirm <id>`.

## Other notes (FYI, no action taken)
- Remaining local branches: `dev`, `main`, `feat/T-30-partial`, `old/2025-spike-do-not-need`.
- `main` is 17 commits behind `origin/dev`. Promoting dev to main only happens on an explicit request, so I left it alone.
- There are no worktrees or stashes to prune, the working tree is clean, and I made no commits or pushes.
- `git branch --merged` would have missed all 8 squash-merged branches. That is why the prune used a content proof.
