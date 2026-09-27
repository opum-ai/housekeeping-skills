---
name: git-hygiene
description: Keep git and GitHub clean the safe way - stage and commit in logical units, push, open and merge PRs, promote dev to main, and prune merged or gone branches (local and remote), worktrees, stashes, and stale refs without ever deleting unlanded work. Use this skill whenever the user asks to commit, push, open or merge a PR, promote a release, or clean up git - "delete merged branches", "prune stale branches", "clean up worktrees", "what are all these branches?", "git is a mess", "remove gone branches", "drop old stashes" - and whenever a housekeeping pass reaches its Land phase. Proves a branch landed (ancestry, squash-merge equivalence, or merged-PR state) before deleting it, and defers to opum-sdlc's branch policy when that skill is installed.
---

# git-hygiene

Two halves:
- **Landing** is commit, push, PR, merge, and promote. You do it directly, following the
  repo's branch policy.
- **Pruning** is branches, worktrees, stashes, and refs. It goes through the `hk` engine,
  because pruning is where irreversible mistakes happen.

**The one rule:** a branch with unique commits is unlanded work, not clutter. It is the
only irreversible mistake in git housekeeping. Nothing here deletes a branch because its
upstream is gone, its name looks old, or it "looks merged". It needs a containment proof.

Engine: the Skill tool printed `Base directory for this skill: <dir>`, so run
`hk() { python3 "<dir>/../../scripts/hk.py" "$@"; }   # a function: works in bash and zsh`.

## Which branch policy applies

1. **The `opum-sdlc` skill is available.** It is the policy. Follow it for:
   - branch names (`<type>/<TASK-ID>-<slug>` off `origin/dev`);
   - the no-exemption rule (docs-only and tracker-only changes still take a branch and a
     PR);
   - squash merge into `dev`;
   - fast-forward-only promotion to `main`;
   - the dangerous set.

   Invoke it before creating a branch, opening or landing a PR, promoting, or deleting any
   branch. Do not restate or override its rules here.
2. **Otherwise**, use the generic flow in `references/generic-flow.md`. Detect the trunk
   (`hk status` reports `trunk` and `release`). Follow the repo's own conventions from
   `CONTRIBUTING.md` and `git log`.

Either way, the **dangerous set** needs the user directly:
- force-push;
- history rewrite;
- a push to the release branch that is not a fast-forward of the reviewed trunk;
- changing remotes or credentials;
- deleting unlanded work.

Everything reversible you may do without asking.

## Landing

### Stage and commit in logical units

At **Minimal**, preserve the work: one WIP commit on the task branch (`WIP: <task id>: where
things stand`) is fine, and so is a clearly named stash if the branch cannot take a commit.
Push it. From **Light** up, commit in logical units, as described below.

1. Survey: `hk status --json` (branch, trunk, uncommitted changes, ahead/behind).
   - **On the trunk or release branch?** Stop and branch first. Commits go on a task
     branch, never on `dev` or `main`. A tracker task exists before the branch in Opum
     repos.
2. Read the diff: `git status`, `git diff`, `git diff --cached`. Group the changes by
   concern, one commit per concern (feature code with its tests; docs; tracker state).
   `git add -A` is how junk and secrets get committed. Stage by path, or by hunk with
   `git add -p` when one file mixes concerns.
3. **Keep out**:
   - **Junk.** Agent junk (`*.bak`, `*_v2.*`, `debug*.log`, scratch scripts,
     `*_SUMMARY.md`). `hk plan --level standard --domains files` lists them. Remove or ignore
     them; don't commit them.
   - **Secrets.** Run `gitleaks protect --staged` if installed. Otherwise grep the staged
     diff for `BEGIN .*PRIVATE KEY`, `AKIA[0-9A-Z]{16}`, `ghp_`, `sk-`, `xox[bp]-`, and
     `password\s*=`. A hit stops the commit until the user decides.
   - **Generated files.** Build outputs and lockfile churn the task didn't cause.
4. **Message**: follow the repo's convention (read `git log --oneline -20`). Put the task
   id in the subject when the repo does (`HS-4: ...` or `feat(tidy): ... (HS-4)`). Add the
   attribution trailer the session instructions specify.
5. **Tracker and docs travel with the code.** In quest/lore repos, commit the `.quest/`
   change and the `lore sync` output in the same commit as the change that caused them
   (the session-sync skill produces them).

### Push

`git push -u origin HEAD` pushes the task branch. If the push is rejected:
- run `git fetch`;
- rebase or merge the *task branch* onto its upstream;
- push again.

Never `--force`. `--force-with-lease` on your own task branch after a rebase is still a
force-push, so ask first.

### Pull request (Standard)

`gh pr create --base <trunk> --fill`, then edit the body. It carries:
- the task id;
- what changed and why;
- the evidence (tests run and their results).

One task, one branch, one PR. Don't stack PRs on another PR's branch: when the parent
merges and its branch is deleted, GitHub closes the child PR.

### Merge (Standard, when the task is finished)

Merge only when:
- the required checks are green **on the head SHA**;
- the repo policy allows it (`gh pr checks <n>`, `gh pr view <n> --json mergeStateStatus`).

Then:
```bash
gh pr merge <n> --squash            # or the repo's merge strategy
git checkout <trunk> && git fetch --prune origin && git pull --ff-only origin <trunk>
git branch -D <task-branch>         # landed via the MERGED PR; -D because a squashed tip is never an ancestor
```
The remote branch deletes itself when `delete_branch_on_merge` is on. **The local one
does not**; nothing deletes it but you. That is why it is part of this step.

If `pull --ff-only` refuses on a local trunk that holds pre-squash commits, **don't run a
bare `git pull`**. It would create a merge commit that breaks fast-forward promotion.
Instead, compare the trees (`git diff <trunk> origin/<trunk> --stat` should be empty),
then realign with `git reset --hard origin/<trunk>`.

### Promote (only when asked)

Promotion of `dev` to `main` happens on an explicit request.
- **opum-sdlc** (see its `references/promotion.md`):
  - open a PR from `dev` to `main` so the checks run on that SHA;
  - land it with `git push origin origin/dev:main`, never with GitHub's merge button;
  - assert tree equality and ancestry afterwards.
- **Generic:** a fast-forward only, then verify that
  `git merge-base --is-ancestor origin/main origin/dev` holds.

## Pruning

```bash
hk plan --level standard --domains git   # --level deep adds stale branches and stashes; add --no-gh if gh is unavailable; the plan notes what it could not prove
```

Read the plan before applying it:
- **`branch.landed` / `remote-branch.landed` (S1).** Each carries its proof: ancestor of
  trunk, content already in trunk (the squash-merge equivalence, via
  `git merge-tree --write-tree`), or a MERGED PR whose merge commit is in trunk. The undo
  is `git branch <name> <sha>`, and it is journalled.
- **`worktree.clean` (S1), `worktree.prunable` (S1).** Worktree removal never uses
  `--force`. A dirty worktree appears as `worktree.dirty`, a **finding**: work hides
  there, so land it first.
- **`stash.old` (Deep, S1).** The stash commit is kept under `refs/archive/stash/<sha>`,
  then dropped. The undo is `git stash store`.
- **`branch.stale-unlanded` (Deep, S3).** Unlanded work idle past `[branches] stale_days`.
  It is archived to `refs/tags/archive/<name>`, then deleted, and **only with the user's
  per-item confirmation**. Before asking, show the unique commits
  (`git log --oneline <trunk>..<branch>`) so the user decides on content, not on a name.
- **Findings (`branch.unlanded`, `remote-branch.unlanded`).** Never planned. Report them
  with their unique commit counts. A remote unlanded branch may be someone else's.

Apply with `hk apply <plan> [--confirm <ids>]`. Anything whose tip moved since planning is
skipped as drift. Report it; don't force it.

**Stale "In Progress" / open-work check (Standard).** In quest repos, the tracker listing only
sees the checked-out branch. Before reporting that nothing is open:
- read the `scope` key of `quest task list --status "In Progress" --json`;
- cross-check `gh pr list --state open`.

`git branch --no-merged` is useless in a squash-merging repo: every landed branch looks
unmerged.

**Estate audit.** When `opum-agent`'s `sdlc-audit` exists (`tooling/sdlc-audit/bin/sdlc-audit.mjs`),
run it before and after a pruning pass and report any disagreement with `hk`'s
classification. Two detectors that agree are evidence; a disagreement is a finding.

## Things that look like cleanup but aren't

- `git clean -fdx` / `-X`: deletes ignored `.env` files and local config. Use the
  workspace-clean skill (it goes through `hk`).
- `git stash clear` / `git stash drop` without archiving: destroys the only copy.
- `git branch --merged | xargs git branch -d`: misses every squash-merged branch and
  proves nothing about the rest.
- `git worktree remove --force`: discards uncommitted work in that tree.
- Deleting branches in **another repository's** checkout: each repo's own session owns
  its refs and `HEAD`. Report instead.
