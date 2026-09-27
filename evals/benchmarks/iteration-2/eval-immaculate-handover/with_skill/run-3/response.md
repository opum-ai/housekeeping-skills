## Housekeeping: Immaculate, repo scope (chosen because: handover to another team tomorrow, and you asked for "immaculate")

Your constraints: you're offline, and nothing that can't be regenerated gets deleted. I used `--no-gh` because there is no network for PR-state proofs. The remote `origin` is a local bare repo (`fixture/remote.git`), so I could still reach it. Branch containment was proven by ancestry against `origin/dev`.

**Recorded**
- No tracker found: no quest, lore, or GitHub remote in this repo. Task ids T-5 and T-9 appear only in commit messages and branch names, so nothing could be updated. This report is the record.

**Landed**
- Nothing new to land. `dev` is at b435ad2 ("T-5: export"), 0 ahead and 0 behind `origin/dev`. No tracked file is modified.
- `main` (037b6e2) is 1 commit behind `dev`, because T-5 is not promoted. I didn't promote it, since that only happens when you ask.

**Cleared** (journal: `fixture/repo/.git/housekeeping/journal/20260927T091231-immaculate.jsonl`; `hk undo <journal>` reverses both items)

| class | items | reclaimed | notes |
|---|---|---|---|
| S1 | 2 | 0 B | local branch `feat/T-5-export` deleted (landed: ancestor of origin/dev; undo `git branch feat/T-5-export b435ad2`). Remote branch `origin/feat/T-5-export` deleted (same proof; undo `git push origin b435ad2:refs/heads/feat/T-5-export`) |
| S2 | 0 | - | not applied: neither item is provably regenerable (see below) |
| S3 | 0 | - | none removed |

**Skipped (deliberately, under your "don't delete anything you can't regenerate")**
- `node_modules/` (80 KB, `fil-8990edce`): `hk` classifies it as regenerable, but no `package.json` or lockfile is tracked on any branch, and you're offline. Nothing could reinstall it, so I kept it.
- `export.py.orig` (22 B, `fil-f867f006`): a junk-named merge leftover, and nothing references it. Its bytes aren't in git, so I kept it. If you want it gone, it goes to the Trash (recoverable) with `hk apply <plan> --only fil-f867f006 --approve-s2`.

**Needs you** (things only you can decide)
- `feat/T-9-experiment`: unlanded commit 09850ee "unfinished experiment" adds `exp.py`. It isn't pushed anywhere, so it exists only in this clone. Before handing over, either land it, push it, or archive it (a Deep pass archives it to `refs/tags/archive/…` with your per-item confirmation).
- `retain/benchmark-baseline` (1a4e726, adds `bench.txt`): protected and kept. It isn't pushed to origin either, so push it if the other team needs the baseline.
- `design-notes.md`: untracked, and looks like real work ("Why export is CSV-only for now"). It isn't in git. Commit it on a docs branch and open a PR into `dev`, or drop it yourself.
- `main` is behind `dev` by T-5: promote before the handover if the team works off `main`.
- HEAD is on the trunk `dev`. That's fine for a handover, but new work should start on a task branch.

**Out of scope, not touched:** Docker (context orbstack; no containers belong to this project) and processes (none running under the fixture besides this session's own shell).

**Verify**: no landed branch is left (a Standard re-plan plans only `export.py.orig`, which was held back as described above). Every tracked file is committed, and every untracked or ignored path is listed below.

### Disposition record (2026-09-27T09:12, commit b435ad2, repo scope): 0 unaccounted of 9

| item | disposition |
|---|---|
| branch feat/T-5-export (local) | removed: landed, ancestor of origin/dev (S1, journalled) |
| branch origin/feat/T-5-export | removed: landed, ancestor of origin/dev (S1, journalled) |
| branch feat/T-9-experiment (1 unlanded commit) | kept: not regenerable and not pushed; you decide whether to land, push, or archive |
| branch retain/benchmark-baseline | kept: reserved `retain/*` prefix (protected) |
| .env | kept: protected keep-list (local secrets), ignored by git |
| .idea/ | accepted: local IDE config, ignored by git, does not travel with the repo |
| node_modules/ (80 KB) | kept: no manifest or lockfile to regenerate from, and you're offline |
| export.py.orig | kept: merge leftover, not regenerable, removal not approved |
| design-notes.md | kept: possible unsaved work; you decide whether to commit or drop |

Final-state checks:

| command | exit |
|---|---|
| `hk disposition --level immaculate --scope repo --no-gh` | 0 (0 unaccounted of 7 engine items; the 2 removed branches are listed above) |
| `[immaculate] verify`: none configured (no `.housekeeping.toml`, and the repo has no install, build, or test) | n/a: no check ran |
| `python3 -c "ast.parse(open('export.py').read())"` (syntax smoke check only) | 0 |
