# Housekeeping levels (agent-facing summary)

This is the operational summary every skill in the plugin uses. The design of record is
`docs/specs/cleanliness-levels.md` ("Housekeeping levels") in the housekeeping-skills repo.

## Contents
- Three settings
- Phases and their order
- What each level adds, per phase
- Scope
- Safety classes
- The protected set
- Branch containment proof
- Dispositions (Immaculate)
- Configuration keys

## Three settings

**Level:**
- `minimal` (1)
- `light` (2)
- `standard` (3, the default)
- `deep` (4)
- `immaculate` (5)

`c1` to `c5` are accepted as legacy aliases.

**Scope:**
- `session`
- `repo` (the default)
- `machine`

**Safety class** (per operation): S0, S1, S2, or S3.

The level decides how much housekeeping to do, and the scope decides where. They are
independent: deep-cleaning the kitchen does not authorize remodeling the house.

## Phases, always in this order

**Survey → Record → Land → Clear → Verify → Report.**
- *Record before clear*: clearing can destroy evidence the record needs.
- *Land before clear*: a branch is removable only once it is landed.

## What each level adds (cumulative)

| Phase | Minimal | Light | Standard (default) | Deep | Immaculate |
|---|---|---|---|---|---|
| Record | progress note: where things stand, what's next | + update the immediate issue; criteria checked with evidence | + reconcile statuses with commits; relevant docs and handoff notes; close a finished task in its delivering PR; gates (`lore check`, `quest agents --check --target claude`, `lore agents --check`, `quest doctor` → `data.healthy`) | + stale statuses (In Progress with no activity, drifted Stories, `lore orphans`, `stale_after`); obsolete docs; two-way spec drift | + disposition for every task and doc touched |
| Land | preserve the work: commit (a WIP commit if needed) and push | logical commits; push | + PR; merge when green; delete the local branch after its merge; promote only on request | | branch state verified |
| Clear | nothing | ledger junk (S1), ledger processes (S1), ledger worktrees (S1), ledger temp (S2) | landed branches, local and remote (S1); prunable worktrees and clean worktrees of landed branches (S1); ignored junk (S1); junk-named untracked files (S2); this project's containers: stop (S1), remove when stopped (S2); repo orphan processes (S2) | stale unlanded branches → archive, then delete (S3); other clean worktrees (S1); old stashes → archive, then drop (S1); build and dependency dirs (S2); `$TMPDIR` prefixes (S2); this project's old scratchpads (S2); project images and networks (S2/S1), volumes (S3); Claude Code bloat proposals | unknown untracked and non-build ignored files: dispose of each (S3 removal, or kept with a reason) |
| Verify | the work is recoverable | no ledger process alive | no landed branch left; gates green; tree clean or explained | bytes reclaimed | `hk disposition` exits 0; `[immaculate] verify` exits 0 |

## Scope

| Scope | Acts on |
|---|---|
| `session` | only what the provenance ledger says this session created, plus landing this session's task branch |
| `repo` | + this repository and this project's containers, processes, and Claude Code state (its memory, scratchpads, and repo settings) |
| `machine` | + global dev caches; all Docker (unused images, stopped containers, build cache, dangling volumes); the plugin cache (orphaned versions, dead in-use markers); transcripts of deleted projects; user settings; other projects' scratchpads; orphaned dev processes outside the repo |

Other repositories' **working trees** are never mutated, in any scope; they are reported
only.

## Safety classes

| Class | Meaning | Gate |
|---|---|---|
| S0 | read-only | none |
| S1 | reversible; undo journalled | allowed within the level and scope |
| S2 | regenerable at a cost | one batch approval (`--approve-s2`, or `--only` a subset) |
| S3 | irreversible | per-item confirmation by name (`--confirm id`); never "yes to all" |

Evidence raises a class; nothing lowers it. Provenance is one of:
- `ledger`: a session recorded creating it;
- `attributed`: tied to this repo by compose label, working directory, or temp prefix;
- `unknown`.

An `unknown` item is raised one class. With no trash tool, trashing becomes a permanent
delete, so a trash item's base class rises from S1 to S2.

## Protected set: never planned, at any level or scope

- **Branches:** trunk, release, and `main`/`master`/`dev`; the checked-out branch; any
  branch checked out in a dirty or locked worktree; `retain/*`, `preserve/*`, and
  `archive/*`, plus `[protect] branches`.
- **Paths:** tracked files, `.git/`, `.env*`, `*.pem`, `*.key`, `id_*`, `.quest/`,
  `.lore/`, `docs/`, `.pi/`, `.housekeeping.toml`, plus `[protect] paths` and
  `[immaculate] keep`.
- **Runtime:**
  - `opum-runner` and `*opum-actions-runner*`, plus `[protect] containers` and
    `[protect] images`;
  - anything labelled `housekeeping.protect=true`;
  - Claude Code, editors, language servers, pm2, and app bundles.
- **Harness:** the current session's scratchpad; plugin versions a live session still
  uses.

## Branch containment proof (R-5)

A branch is landed only when all of these hold:
- the refs were fetched with `--prune` in this pass;
- one containment proof holds against the trunk or release branch:
  - **ancestry**: `git merge-base --is-ancestor`;
  - **squash equivalence**: `git merge-tree --write-tree trunk tip` equals the trunk's
    tree;
  - **PR state**: a MERGED PR whose head is the tip and whose merge commit is in the
    trunk;
- no dirty or locked worktree has it checked out. A clean worktree is removed first, in the
  same apply.

"Upstream gone" is evidence, not proof. An unlanded branch is only ever archived to
`refs/tags/archive/<name>` and then deleted, as S3.

## Dispositions (Immaculate)

`hk disposition --level immaculate --scope <s>` lists every in-scope item. Record each
disposition with `--set <id>=<kind>:<reason>`, where `kind` is one of:
- `kept`, with the reason;
- `removed`;
- `landed`;
- `deferred`, to a task id;
- `accepted`, a known, deliberate state.

Protected and keep-list items are auto-kept. The command exits 0 only when nothing is
unaccounted for. Dispositions persist in `.git/housekeeping/dispositions.json`. Put a
summary on the task, and the full record in the PR body.

## `.housekeeping.toml` keys

- `housekeeping_level`, `housekeeping_scope`.
- `[levels]`: `checkpoint`, `session_end`, `default`, `task_done`.
- `[sdlc]`: `trunk`, `release`, `merge`, `remote`.
- `[protect]`: `branches`, `paths`, `containers`, `images`. These extend the built-ins;
  they never replace them.
- `[junk] patterns`.
- `[tmp]`: `prefixes`, `max_age_days`.
- `[stash] max_age_days`.
- `[branches] stale_days`.
- `[scratchpad] max_age_days`.
- `[provenance] enabled`.
- `[immaculate]`: `keep`, `verify`.
- `[docker] projects`.
