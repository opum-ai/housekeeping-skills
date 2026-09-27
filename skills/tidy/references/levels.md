# Cleanliness levels (agent-facing summary)

This is the operational summary every skill in the plugin uses. The design of record is
`docs/specs/cleanliness-levels.md` in the housekeeping-skills repo.

## Contents
- Phases and their order
- What each level adds, per phase
- Reach per level
- Safety classes and how evidence moves them
- The protected set
- Branch containment proof
- Configuration keys

## Phases, always in this order

**Survey → Record → Land → Clear → Verify → Report.**
- *Record before clear*: clearing can destroy the evidence a record needs.
- *Land before clear*: a branch is removable only once it is landed.
- A pass interrupted part-way has done the durable half.

## What each level adds (cumulative)

| Phase | C1 Tidy | C2 Sweep | C3 Clean | C4 Deep clean | C5 Clean room |
|---|---|---|---|---|---|
| Record | progress note; criteria checked with evidence | + update docs the session touched; follow-up tasks; stash review | + close the task in the delivering PR; `lore check`, `quest agents --check --target claude`, `lore agents --check`, `quest doctor` (read `data.healthy`) | + two-way spec-drift reconciliation | + clean-room certificate on the task |
| Land | logical commits on the task branch; push | + open/refresh the PR | + squash-merge when green; delete the local branch; promote only on request | | |
| Clear | nothing (report findings) | ledger junk (S1); ledger processes (S1); ledger clean worktrees (S1); ledger temp (S2) | landed branches, local and remote (S1); prunable worktrees (S1); clean worktrees (S1); ignored junk (S1); project containers: stop (S1), remove (S2); repo orphans (S2) | build/dependency dirs (S2); project images and networks (S2/S1); volumes (S3); stale unlanded branches → archive then delete (S3); old stashes → archive then drop (S1); `$TMPDIR` prefixes (S2); old scratchpads, this project (S2); orphaned plugin versions and dead in-use markers (S2); transcripts of deleted projects (S3); memory, CLAUDE.md, permission, and hook proposals (approval) | everything ignored minus the keep-list (S3 unless known build output); untracked unknown files (S3); global caches (S2); machine Docker minus protected (S2; volumes S3); foreign orphans (S3); every project's old scratchpads (S2) |
| Verify | tree clean or explained; pushed | no ledger process alive | no landed branch left; gates green | bytes reclaimed | **rebuild from scratch exits 0** |

## Reach

| Level | May mutate |
|---|---|
| C1 | the repo's index and task branch, the tracker, the remote task branch |
| C2 | + what this session created (ledger) |
| C3 | + the repo's branches, worktrees, and refs; this project's containers |
| C4 | + the repo's ignored outputs; this project's Docker images, networks, and volumes; the user-level Claude Code harness; `$TMPDIR` entries attributed to this repo |
| C5 | + global caches, machine-wide Docker, the whole checkout |

Other repositories' working trees are never mutated, even at C5.

## Safety classes

| Class | Meaning | Gate |
|---|---|---|
| S0 | read-only | none |
| S1 | reversible; the undo is journalled | allowed within the level |
| S2 | regenerable at a cost | one batch approval |
| S3 | irreversible | per-item confirmation by name; never "yes to all" |

Evidence raises a class; nothing lowers it. Provenance is one of:
- `ledger`: a session recorded creating it;
- `attributed`: tied to this repo by compose label, working directory, or temp prefix;
- `unknown`.

An `unknown` item is raised one class. With no trash tool, trashing becomes a permanent
delete, so a trash item's base class rises from S1 to S2.

## Protected set: never planned, at any level

- **Branches:** trunk, release, and `main`/`master`/`dev`; the checked-out branch; any
  branch checked out in a worktree; `retain/*`, `preserve/*`, `archive/*`, plus
  `[protect] branches`.
- **Paths:** tracked files, `.git/`, `.env*`, `*.pem`, `*.key`, `id_*`, `.quest/`,
  `.lore/`, `docs/`, `.pi/`, `.housekeeping.toml`, plus `[protect] paths` and the
  clean-room keep-list.
- **Runtime:** `opum-runner` and `*opum-actions-runner*`, plus `[protect] containers` and
  `images`; the label `housekeeping.protect=true`; Claude Code, editors, language servers,
  pm2, and app bundles.
- **Harness:** the current session's scratchpad; plugin versions a live session still
  uses.

## Branch containment proof (R-5)

A branch is landed only when all of these hold:
- The refs were fetched with `--prune` in this pass.
- One containment proof holds against the trunk or the release branch:
  - **ancestry**: `git merge-base --is-ancestor`;
  - **squash equivalence**: `git merge-tree --write-tree trunk tip` equals trunk's tree;
  - **PR state**: a MERGED PR whose head is the tip and whose merge commit is in the
    trunk.
- It is not checked out anywhere.

"Upstream gone" is evidence, not proof. An unlanded branch is only ever archived to
`refs/tags/archive/<name>` and then deleted, as S3.

## `.housekeeping.toml` keys

- `[levels]`: `default`, `session_end`, `task_done`.
- `[sdlc]`: `trunk`, `release`, `merge`, `remote`.
- `[protect]`: `branches`, `paths`, `containers`, `images`. These extend the built-ins;
  they never replace them.
- `[junk] patterns`.
- `[tmp]`: `prefixes`, `max_age_days`.
- `[stash] max_age_days`.
- `[branches] stale_days`.
- `[scratchpad] max_age_days`.
- `[provenance] enabled`.
- `[cleanroom]`: `keep`, `verify`.
- `[docker] projects`.
