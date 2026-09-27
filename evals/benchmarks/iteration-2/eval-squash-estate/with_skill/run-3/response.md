# Merged-branch prune: fixture/repo

Skill used: **git-hygiene** (pruning half), driven through the `hk` engine at **Standard**
level, git domain only. You asked to prune what is merged, and Standard covers exactly that.
Trunk detected: `dev` (release: `main`). The repo squash-merges, so `git branch --merged` would
have shown nothing. Each deletion below needed a containment proof instead.

## Deleted (8 local branches, all proven landed)

Proof for each: the squash-merge equivalence. `git merge-tree --write-tree origin/dev <branch>`
produces exactly origin/dev's tree (`86f4fc9`), so everything on the branch is already in dev.
I checked this myself as well as trusting the engine. Every remote upstream was also gone,
but that only counts as supporting evidence, not proof.

| branch | tip (undo point) | landed as |
|---|---|---|
| feat/T-10-change-0 | 4615b34 | 99002fd T-10: change 0 (#100) |
| feat/T-11-change-1 | 42ce3fa | c051861 T-11: change 1 (#101) |
| feat/T-12-change-2 | e245284 | 8a8df18 T-12: change 2 (#102) |
| feat/T-13-change-3 | 6426a38 | 6f8699d T-13: change 3 (#103) |
| feat/T-14-change-4 | 33d538e | 761c88e T-14: change 4 (#104) |
| feat/T-15-change-5 | e694f51 | 01323f1 T-15: change 5 (#105) |
| feat/T-16-change-6 | 329012c | 989341f T-16: change 6 (#106) |
| feat/T-17-change-7 | fa2a28b | f5339cc T-17: change 7 (#107) |

Undo: every deletion is journalled. To restore all of them, run
`python3 <plugin>/scripts/hk.py undo <workspace>/iteration-2/eval-squash-estate/with_skill/run-3/fixture/repo/.git/housekeeping/journal/20260927T091136-standard.jsonl`.
To restore one, run `git branch <name> <sha>`.

## Left alone: needs you

1. **`feat/T-30-partial` (local + `origin/feat/T-30-partial`): NOT merged.** Only half of it
   landed. dev has `8ebe406 partial: landed half` (adds `p1.txt`). The branch still has one
   unique commit, `9090805 partial: the half that never landed` (adds `p2.txt`), which is not in
   dev. This is unlanded work, so I did not delete it locally or on the remote. Next step: open a
   PR for the remaining commit, or tell me it is intentionally dropped. If you drop it, archive it
   first (`git tag archive/feat/T-30-partial 9090805`), then delete it.
2. **`old/2025-spike-do-not-need`: NOT merged.** It has one unique commit, `8175506 spike nobody
   merged` (adds `spike.txt`), last touched 2025-11-01 and never pushed. The name says you don't
   need it, but a name is not a proof, and you only authorized merged branches. A Deep-level plan
   lists it as `branch.stale-unlanded` (S3, irreversible). That needs your per-item
   confirmation, and I could not get it while you were away. To remove it, run
   `hk plan --level deep --domains git`, then `hk apply <plan> --confirm <id>`. The engine
   archives it to `refs/tags/archive/old/2025-spike-do-not-need` before deleting it. Or delete it
   by hand with `git branch -D` if you're sure.

## Not touched: out of scope for this request

- `dev`, `main`: the trunk and release branches. Both are in sync with origin. I did no
  promotion, because you didn't ask for one.
- No stashes or extra worktrees exist. The working tree was clean before and after, and I made
  no commits or pushes. I ran no remote-side deletions; `hk plan` ran `git fetch --prune`, which
  touches only remote-tracking refs.
- I skipped GitHub PR-state proofs (`--no-gh`), because this remote is a local bare repo with no
  PRs. The squash-equivalence proof was enough for all 8 branches.

## Final state

```
* dev                         8ebe406 [origin/dev] partial: landed half
  feat/T-30-partial           9090805 [origin/feat/T-30-partial] partial: the half that never landed
  main                        7b8ec78 [origin/main] ignore build outputs
  old/2025-spike-do-not-need  8175506 spike nobody merged
```

Engine note: at Standard, the plan does not mention `old/2025-spike-do-not-need` at all. It
isn't listed even as a finding, and it only appears at Deep. I found it by reviewing
`git branch -vv` myself. You may want Standard to surface it as an `unlanded` finding.
