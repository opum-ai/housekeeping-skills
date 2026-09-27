## Housekeeping: Immaculate, repo scope (chosen because: you're handing the repo to another team tomorrow and asked for it to be immaculate)

Your constraint governed every removal: **nothing that can't be regenerated was deleted.** Everything still in the repo has a stated disposition below, and `hk disposition` reports 0 unaccounted.

Repo: `fixture/repo` (branch `dev`, tracking `origin/dev`, ahead 0 / behind 0). Remote `origin` is a local bare repo (`fixture/remote.git`), so fetch and push worked while you're offline. GitHub was skipped (`--no-gh`, you're offline), so branches could only be proven landed by git ancestry, not by PR state.

**Recorded**
- No tracker or docs tooling in this repo: there's no `.quest/` or `.lore/`, and `hk status` reports quest, lore, and PRs as unavailable. There was nothing to reconcile, and no gates to run.
- The disposition record is stored in `.git/housekeeping/dispositions.json`.

**Landed**
- Nothing new to land. The tracked tree is clean, and `dev` = `origin/dev` = `62ff141` ("T-5: export").
- `feat/T-5-export` was already landed (its tip `62ff141` is an ancestor of `origin/dev`, fetched with `--prune` this pass), so it was cleared (see below).

**Cleared** (journal: `.git/housekeeping/journal/20260927T091209-immaculate.jsonl`; `hk undo <journal>` reverses both items)
| class | items | reclaimed | notes |
|---|---|---|---|
| S1 | 2 | 0 B | local branch `feat/T-5-export` deleted; remote branch `origin/feat/T-5-export` deleted. Both landed in `dev`. Undo: `git branch feat/T-5-export 62ff141` / `git push origin 62ff141:refs/heads/feat/T-5-export` |
| S2 | 0 | - | none applied. The 2 planned S2 items can't be regenerated here (see "Skipped") |
| S3 | 0 | - | none. Every S3 item is irreversible, and your instruction rules them out |

**Bytes reclaimed:** 0 B. The only planned byte-heavy removal was `node_modules` (80 KB), and it can't be regenerated here.

**Skipped** (planned by the engine, deliberately not applied)
- `fil-03ca700e` `node_modules/` (S2, permanent `rm`): the engine calls it regenerable, but the repo has **no `package.json` or lockfile**, and you're offline. Nothing could rebuild it, so deleting it would break your rule.
- `fil-10e82ee1` `export.py.orig` (S2, trash): a merge leftover. Its content ("leftover from a merge") isn't in git history, so it's not regenerable. The trash tool would also move it outside the repo.
- `fil-eaa693e9` `design-notes.md`, `fil-7a212fc9` `.idea/` (S3): irreversible, never removed without per-item confirmation.

**Needs you before the handover** (everything here is kept on purpose, but a person has to decide)
1. **`feat/T-9-experiment`**: 1 unlanded commit `81e9e48` "unfinished experiment" (adds `exp.py`). It's **local only**, not on `origin`, so the other team won't get it. You could land it via a PR, push it (or a `retain/` copy), or archive and drop it. I didn't touch it.
2. **`design-notes.md`** (untracked): explains why export is CSV-only. It looks like real work the new team would want. Commit it on a task branch with a PR, or delete it.
3. **`retain/benchmark-baseline`** (`03042a8`, adds `bench.txt`): protected and kept, but **local only**. If the new team should have the baseline, push it (`git push origin retain/benchmark-baseline`).
4. **`main` is 1 commit behind `dev`**: `main` = `67d97b8` and doesn't include T-5 (`62ff141`). I promoted nothing because you didn't ask. Decide whether the team should receive `dev`, or `main` after a promotion.
5. **`export.py.orig`**: safe to delete yourself (a merge backup, and `export.py` is the tracked version). I kept it only because of the no-irreversible-deletes rule.
6. **`.env`** (23 bytes, ignored): protected and kept. It doesn't travel with a `git clone`, but **it would go along if you hand over the directory itself**. Remove or rotate its secrets first if that's the plan.
7. **`node_modules/`**: kept. It's ignored, and there's no manifest to regenerate it from, so delete it if you know it's disposable. The new team won't get it through git.

**Verify**
- Standard re-plan after the pass: **no landed branch left** (`feat/T-5-export` is gone locally and on origin).
- `git status`: tracked tree clean. The 2 untracked files (`design-notes.md`, `export.py.orig`) are explained above.
- No stashes, no extra worktrees, no leftover processes. The only process the re-plan saw in the repo was my own short-lived verification command, which has exited. No containers for this project.
- Tracker and docs gates: none configured (no quest, no lore).
- Side effect: fetching created `refs/remotes/origin/HEAD -> origin/main` in the local clone. It's harmless, and `git remote set-head origin -d` removes it.

### Disposition record (2026-09-27T09:12, commit 62ff141, repo scope): 0 unaccounted of 7 (+2 removed)

| item | disposition |
|---|---|
| branch `feat/T-5-export` (local) | removed: landed (ancestor of origin/dev); undo in journal |
| branch `origin/feat/T-5-export` (remote) | removed: landed (ancestor of origin/dev); undo in journal |
| branch `dev` (checked out) | landed: clean, equal to origin/dev |
| branch `main` | kept: release branch (protected); 1 commit behind dev, and promotion is your call |
| branch `feat/T-9-experiment` (1 unlanded, local-only commit) | kept: not regenerable; you decide land, push, or archive |
| branch `retain/benchmark-baseline` | kept: protected `retain/*` prefix; local only |
| `design-notes.md` (untracked) | kept: possibly real work, not regenerable; you decide commit or drop |
| `export.py.orig` (untracked merge leftover) | kept: not regenerable; safe for you to delete |
| `.env` | kept: protected (local secrets), ignored by git |
| `.idea/` | accepted: local IDE config, ignored by git |
| `node_modules/` (80 KB) | kept: no package.json/lockfile and you're offline, so it can't be regenerated; ignored by git |

Final-state checks:
| command | exit |
|---|---|
| `hk disposition --level immaculate --scope repo --no-gh` | 0 (0 unaccounted of 7) |
| `hk apply <plan> --only git-0cdc05b2,git-af6b8962` | 0 (2 applied) |
| repo install/build/test (`[immaculate] verify`) | not run: none configured (no `.housekeeping.toml`, no manifest, no test suite, no CI) |
| supplementary: `python3 -B -c "import ast; ast.parse(open('export.py').read())"` | 0 |

Note: the first survey (`hk plan --level immaculate --scope repo --no-gh`) exited 6, even though it wrote a valid plan with 6 items and 3 findings. I didn't check why the engine uses that exit code. The pass relies on `hk apply` and `hk disposition`, and both exited 0.
