---
# yaml-language-server: $schema=../../.lore/schemas/spec.schema.json
type: Spec
title: Cleanliness levels
tags:
  - housekeeping
  - levels
  - safety
status: draft
summary: Five cumulative cleanliness levels, C1 Tidy to C5 Clean room, crossed with four per-operation safety classes S0-S3, a protected set, and graduated reach.
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:21:58.931Z
---

# Cleanliness levels

## Summary

Housekeeping has two independent dials. Every skill in this plugin reads both.

- **The cleanliness level (C1-C5)** says *how far* a pass reaches. It runs from the
  daily chore of recording and committing up to a clean-room deep scrub. Choosing a
  higher level widens what is in scope. Each level includes everything below it.
- **The safety class (S0-S3)** says *how each individual operation is gated*. It is a
  property of the operation and its evidence, never of the level. A C5 pass does not make
  an irreversible deletion any less irreversible, so it does not remove the confirmation.

| Level | Name | One line |
|---|---|---|
| **C1** | **Tidy** | Record progress and land the work: tracker notes, logical commits, push. Touches only this session's work. |
| **C2** | **Sweep** | Also clear what this session left lying around: its junk files, its processes and dev servers, its clean worktrees, and the docs it touched. |
| **C3** | **Clean** | Also finish the task and prune what it leaves behind: merge per the SDLC, prune landed branches, prunable worktrees, stale refs, this project's containers, and orphaned processes in the repo. Run the tracker and docs gates. |
| **C4** | **Deep clean** | Also reclaim regenerable weight: build outputs, dependency dirs, project caches, project Docker images, old stashes, stale branches (archived first), and user-level agent-harness debris. |
| **C5** | **Clean room** | Also reset the checkout to fresh-clone state, prune global caches and Docker, then **prove** it rebuilds from scratch and certify what remains. |

The chores-to-clean-room metaphor is deliberate. C1 is washing the dishes after dinner.
C5 is the clean room you enter before a release, a benchmark, or a handover to another
team: you can account for every item left in it.

## Requirements

### R-1: Durable before disposable

A pass always runs its phases in this order:

1. **Survey.** An S0 inventory.
2. **Record.** Tracker and docs.
3. **Land.** Commit, push, PR, merge, promote.
4. **Clear.** Removals.
5. **Verify.**
6. **Report.**

Recording comes first because clearing can destroy the evidence a record needs: logs,
scratch output, the worktree holding an uncommitted fix. Landing comes before clearing
because a branch is only removable once it is landed. A pass interrupted part-way leaves
the durable half done.

### R-2: Levels are cumulative and scoped by reach

A level adds scope. It never skips a lower level's obligations. A C4 pass also records and
lands. Each level has a **reach**: the set of places it may mutate.

| Level | May mutate | Reports only |
|---|---|---|
| C1 | the current repo's index, branch, and tracker; the remote task branch | everything else |
| C2 | + untracked files and processes this session created (ledger or attribution) | |
| C3 | + the repo's local and remote branches, worktrees, and refs; this project's containers | other repos |
| C4 | + the repo's ignored build outputs and caches; this project's Docker images, networks, and volumes (S3); the user-level harness (`~/.claude`, session scratchpads, `$TMPDIR` entries attributed to this repo) | other repos' working trees |
| C5 | + global dev caches and machine-wide Docker (minus the protected set); the whole checkout to fresh-clone state | **other repos' working trees are never mutated, at any level** |

Other repositories' working trees stay out of reach even at C5. Each repository has one
live session that owns its mutations. Moving another repo's `HEAD`, index, or tree
without that session seeing it is how commits race onto the wrong branch. C5 **reports**
their state; their own sessions clean them.

### R-3: Every operation carries a safety class

| Class | Meaning | Examples | Gate |
|---|---|---|---|
| **S0 Observe** | read-only | inventory, `git fetch --prune`, `docker system df`, `claude doctor`, `lore check` | none |
| **S1 Reversible** | undo is cheap, local, and recorded in the journal | move to trash; stop (not remove) a container; delete a *landed* branch after recording its SHA; export a stash to a patch before dropping it; remove a *clean* worktree whose branch persists; stop a process the ledger says this session started | allowed within the chosen level; listed in the plan |
| **S2 Regenerable** | data is destroyed, but a source of truth regenerates it at a cost | build outputs, `node_modules`, `.venv`, tool caches, unused Docker images and build cache, orphaned plugin-cache versions | shown in the plan, then approved **once as a batch** |
| **S3 Irreversible** | unique data could be lost | a branch with unique unlanded commits; a dirty worktree; dropping a stash without export; a Docker volume; an untracked file that is neither ignored nor in the ledger; purging transcripts or memories; force-push; history rewrite | confirmed **per item, by name**; never "yes to all"; never implied by the level |

**The evidence raises the class; nothing lowers it.**
- *Provenance* is one of `ledger` (this session recorded creating it), `attributed`
  (repo-scoped by compose label, working directory, or a configured temp prefix), or
  `unknown`.
- An `unknown` item is raised one class, capped at S3.
- A junk-looking file the session did not create is therefore S2: approved as a batch after
  review, never swept silently.
- With no trash tool, trashing is a permanent delete, so a trash item's base class rises
  from S1 to S2.

### R-4: The protected set is never planned for removal

At any level, the engine refuses to plan these:
- **Branches:** the trunk and release branches (`dev`, `main`, `master`, or as
  configured); the checked-out branch; any branch checked out in a worktree; the prefixes
  `retain/`, `preserve/`, `archive/`.
- **Paths:** tracked files; `.git/`; `.env*`; `*.pem`, `*.key`, `id_*`; `.quest/`;
  `.lore/` config; anything under `docs/`; `.pi/`.
- **Runtime:** containers and images named in `protect.containers` / `protect.images`, in
  every Docker context. The built-in entry is the self-hosted CI runner `opum-runner` and
  its image. Also anything labelled `housekeeping.protect=true`.
- **Harness:** the current session's transcript and scratchpad; managed settings.
- **Everything else outside the level's reach.**

A protected item may still appear in the report as a finding. It is never in the plan.

### R-5: A branch with unique commits is unlanded work, not clutter

This is the only irreversible mistake in git housekeeping, so the proof bar is explicit.
A local or remote branch is removable as **landed** only when all of these hold:

1. The remote-tracking refs were fetched with `--prune` in this pass.
2. At least one of these containment proofs holds against the integration branch:
   - ancestry: `git merge-base --is-ancestor <tip> origin/<trunk>`;
   - squash equivalence: the merge-tree of the branch onto the trunk equals the trunk's
     tree;
   - PR state: a `MERGED` PR whose merge commit is an ancestor of `origin/<trunk>`.
3. No worktree has it checked out with uncommitted changes.

"Upstream gone" is **not** a containment proof. A branch that fails the proof is
`UNLANDED`. Removing it is S3 and requires an `archive/<name>` ref or tag first.

When `opum-sdlc` is installed, its rules govern branch naming, merge strategy, and
promotion. This spec only adds the classification and the gate.

### R-6: Apply exactly what was reviewed

Removals go through the engine's plan/apply cycle (ADR-0003):
- `hk plan` writes a plan with a fingerprint per item (SHA, mtime and size, container ID).
- `hk apply` re-checks each fingerprint. It skips any item that changed since planning,
  runs only S3 items whose IDs were confirmed, and appends every action with its undo
  recipe to a journal.
- A skill never deletes through an ad-hoc generated script. It never uses
  `rm -rf "$VAR"` on a path it has not resolved and containment-checked. It never
  defaults to `git clean -X`, which deletes ignored `.env` files.

### R-7: Record and land follow the tracker and docs contracts

- **Quest.** Every write declares `--actor <id> --actor-kind delegated-agent
  --accountable-human <id>`.
- **Criteria.** Acceptance criteria are checked only with evidence in hand.
- **Closing.** A task is closed with `quest task complete`, never `task edit --status
  Done`. Close it in the PR that delivers its last criterion, citing the PR number and CI
  run ID, not the merge SHA.
- **Lore.** After any tracker status move, run `lore sync`, then `lore check`. Commit the
  output with `.quest/` and the code in the same commit.
- **"Nothing In Progress" is branch-scoped.** Read the `scope` key of
  `quest task list --json`, and cross-check `gh pr list --state open` before reporting a
  clear state.

### R-8: Every pass reports

Every pass ends with a report of:
- the level and how it was chosen;
- each phase's actions, with class and result;
- skipped items and why;
- bytes reclaimed;
- the journal path for undo;
- open findings outside reach.

A C5 pass also produces a **clean-room certificate**: the rebuild-from-scratch commands
and their exit codes, and the remaining inventory, with a reason for every item left.

## Design

### What each level adds

Each row is phased as in R-1. Cells are cumulative: a level also does everything to its
left.

| Phase | C1 Tidy | C2 Sweep | C3 Clean | C4 Deep clean | C5 Clean room |
|---|---|---|---|---|---|
| **Record** | progress note on the In Progress task; criteria checked with evidence | + update lore docs the session touched; file follow-up tasks for discovered work; stash review | + close the task in the delivering PR; `lore check`, `quest agents --check`, `lore agents --check`, `quest doctor` (read `data.healthy`) | + spec-drift reconciliation across the epic (two-way: fix code, amend spec, or record a deviation) | + record the clean-room certificate on the task |
| **Land** | logical commits on the task branch; push the branch | + open or refresh the PR | + squash-merge when checks are green; promote only when the user asked and the promotion conditions hold | | |
| **Clear** | none (findings reported) | ledger-owned junk (S1); processes and dev servers this session started (S1); clean worktrees this session created (S1) | landed branches, local and remote (S1); stale refs (S0); prunable and clean worktrees (S1); ignored junk (S1); this project's containers: stop (S1), remove when stopped (S2); orphaned processes attributed to the repo (S2) | build outputs and dependency dirs (S2); project caches (S2); project images and networks (S2); volumes (S3); stale unlanded branches, archived then deleted (S3); stashes older than the configured age, exported then dropped (S1); `$TMPDIR` entries with configured prefixes (S2); old session scratchpads (S2); orphaned plugin-cache versions (S2); transcripts of deleted project paths via `claude project purge --dry-run` (S3); proposals for memory, CLAUDE.md, permission and hook hygiene (applied only on approval) | checkout reset to fresh-clone state minus the keep-list (known build outputs S2; every other ignored or untracked path S3); global caches via their official prune commands (S2); machine-wide Docker prune minus the protected set (S2, volumes S3); remaining orphaned processes (S3) |
| **Verify** | tree clean or remaining changes explained; branch pushed | no ledger process alive; no ledger junk left | no removable-landed branches left; gates green | reclaimed bytes measured | rebuild from scratch (install, build, test) exits 0 |

### Choosing a level

When the user names a level, use it. Otherwise infer the level from context, state it in
the plan, and let the user raise or lower it:

1. The session is ending, compacting, or handing off → **C1**.
2. A bare "clean up", "tidy up", or "sweep" → **C2**.
3. A task has just finished, a PR merged, or "finish/close out this branch" → **C3**.
4. Disk space, "deep clean", or a slow machine → **C4**.
5. "Pristine", "clean room", or "scrub"; before a release, benchmark, or demo → **C5**.

`.housekeeping.toml` may set the defaults for these contexts. An agent may always choose
a *lower* level than inferred when it is unsure. Going *higher* than the user asked
requires asking.

### Configuration

`.housekeeping.toml` sits at the repository root and is committed. Every key is optional.
The engine's built-in defaults apply without the file.

```toml
version = 1

[levels]                      # context -> level
default = "C2"
session_end = "C1"
task_done = "C3"

[sdlc]                        # auto-detected when omitted
trunk = "dev"                 # integration branch; else origin/HEAD
release = "main"
merge = "squash"

[protect]                     # extends the built-in protected set
branches = ["retain/*", "preserve/*", "archive/*"]
paths = [".env*", "*.pem", "*.key"]
containers = ["opum-runner"]
images = ["*opum-actions-runner*"]

[junk]                        # extra agent-junk patterns (untracked files)
patterns = []

[tmp]                         # $TMPDIR entries attributed to this repo
prefixes = []
max_age_days = 2

[stash]
max_age_days = 30

[provenance]                  # opt-in capture hook
enabled = false

[cleanroom]
keep = [".env", ".env.local"]
verify = []                   # e.g. ["npm ci", "npm test"]
```

### The engine and the skills

The skills make judgement calls. The engine (`scripts/hk.py`, stdlib Python 3.9+) does
the deterministic work: inventory, classification, planning, applying, journalling, and
undo. Commit, PR, merge, and promotion are *landing* operations. The skills perform them
directly under `opum-sdlc`. The engine only probes their state.

| Skill | Phases it owns |
|---|---|
| `tidy` | chooses the level; runs the phases in order; writes the report |
| `session-sync` | Record |
| `git-hygiene` | Land; the git part of Clear |
| `workspace-clean` | Clear for files, temp, builds, caches |
| `runtime-clean` | Clear for containers, processes, ports, background tasks |
| `harness-hygiene` | Clear and audit for the Claude Code harness |

## Open questions

- **Clean-room keep-list.** Should C5 detect per-ecosystem keep-worthy ignored files
  (IDE settings, local certs) automatically, or rely only on `[cleanroom] keep`? The
  proposal is the explicit list plus the protected path set, and to report every other
  ignored file before removing it.
- **Estate audit.** Should the engine read `sdlc-audit --json` when opum-agent is present
  instead of classifying branches itself? The proposal is to classify natively (it must
  work outside the fleet) and cross-check against `sdlc-audit` when it is available,
  reporting any disagreement.
