---
# yaml-language-server: $schema=../../.lore/schemas/spec.schema.json
type: Spec
title: Housekeeping levels
tags:
  - housekeeping
  - levels
  - safety
status: draft
summary: "Five cumulative housekeeping levels, Minimal to Immaculate (default Standard), with scope (session, repo, machine) as a separate setting and four per-operation safety classes S0-S3."
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:21:58.931Z
---

# Housekeeping levels

## Summary

This plugin does **project housekeeping**: commits, branches, worktrees, caches, containers,
issue statuses, documentation, and handoffs. It does **not** improve the code itself.
Formatting, dead code, and refactors belong to other tools.

Three independent settings govern every pass. Every skill reads all three:

- **The housekeeping level** (`housekeeping_level`) says *how much* housekeeping to do.
  Each level includes everything below it.
- **The scope** (`housekeeping_scope`: `session | repo | machine`) says *where* the pass
  may act. Scope is independent of level: deep-cleaning the kitchen does not authorize
  remodeling the house.
- **The safety class** (S0-S3) of each operation says *how it is gated*. It is a property of
  the operation and its evidence, never of the level or the scope.

| Level | Name | Meaning for project housekeeping |
|---|---|---|
| **1** | **Minimal** | Preserve the work and record where things stand. Do only what is necessary to leave a recoverable stopping point. |
| **2** | **Light** | Put away what you just used. Commit completed work as appropriate, update the immediate issue, and remove task-generated temporary files. |
| **3** | **Standard** (default) | Complete the routine housekeeping checklist. Reconcile commits and issue statuses, update relevant documentation and handoff notes, and remove known disposable artifacts. |
| **4** | **Deep** | Check the places routine housekeeping misses. Review stale branches and worktrees, disposable caches, outdated status information, obsolete documentation, and leftover artifacts. Resolve what is safe and authorized. |
| **5** | **Immaculate** | Complete the deep housekeeping **and verify the final state**. Every in-scope change, branch, issue, document, and artifact has an intentional disposition. Nothing remains forgotten, ambiguous, or unaccounted for. |

The dividing line at the top is **"perform the chores" versus "verify that no applicable
chores remain."**

> **Immaculate:** complete and verify all applicable housekeeping within the authorized
> scope. Preserve intentional work and required artifacts; explicitly account for anything
> that cannot or should not be removed.

The goal is **nothing left unattended, not nothing left on disk.** Immaculate is not a purge.
A kept `.env`, a `retain/` branch, or an open task deferred to a follow-up is immaculate, as
long as it has a stated disposition.

Why these names:
- **Absolute** implies an unconditional guarantee.
- **Strict** describes how firmly rules are enforced, not how much gets done.
- **Maximum** does not describe the result.
- **Pristine** suggests an untouched state.
- **Sterile** and **clean room** emphasize removing contamination.

**Immaculate** allows a project to be in active use and completely in order.

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

### R-2: Levels are cumulative; scope is a separate setting

A level adds chores and never skips a lower level's obligations. Scope bounds where any
level may act:

| Scope | May act on |
|---|---|
| `session` | only what this session created (provenance ledger), plus landing this session's task branch |
| `repo` (default) | + the current repository: its index, branches, worktrees, refs, ignored outputs, and tracker; this project's containers and processes; this project's Claude Code state (its memory, scratchpads, repo settings) |
| `machine` | + user- and machine-wide state: global dev caches, all Docker, the Claude Code plugin cache, transcripts of deleted projects, user settings, other projects' scratchpads, orphaned processes outside the repo |

- **Other repositories' working trees are never mutated, at any level or scope.** Each
  repository has one live session that owns its mutations. Moving another repo's `HEAD`,
  index, or tree without that session seeing it is how commits race onto the wrong branch
  (ADR-0005). Machine scope *reports* them.
- A level never widens the scope. "Deep clean" means a deep pass at the configured scope
  (repo by default). Machine-wide purges happen only when machine scope is asked for.

### R-3: Every operation carries a safety class

| Class | Meaning | Examples | Gate |
|---|---|---|---|
| **S0 Observe** | read-only | inventory, `git fetch --prune`, `docker system df`, `claude doctor`, `lore check` | none |
| **S1 Reversible** | undo is cheap, local, and recorded in the journal | move to trash; stop (not remove) a container; delete a *landed* branch after recording its SHA; archive a stash under a ref, then drop it; remove a *clean* worktree whose branch persists; stop a process the ledger says this session started | allowed within the chosen level and scope; listed in the plan |
| **S2 Regenerable** | data is destroyed, but a source of truth regenerates it at a cost | build outputs, `node_modules`, `.venv`, tool caches, unused Docker images and build cache, stopped containers, orphaned plugin-cache versions | shown in the plan, then approved **once as a batch** |
| **S3 Irreversible** | unique data could be lost | a branch with unique unlanded commits; dropping a stash without archiving; a Docker volume; an untracked file that is neither ignored nor in the ledger; purging transcripts or memories; force-push; history rewrite | confirmed **per item, by name**; never "yes to all"; never implied by the level |

**The evidence raises the class; nothing lowers it.**
- *Provenance* is one of `ledger` (this session recorded creating it), `attributed`
  (repo-scoped by compose label, working directory, or a configured temp prefix), or
  `unknown`.
- An `unknown` item is raised one class, capped at S3. A junk-looking file the session did
  not create is therefore S2: approved as a batch after review, never swept silently.
- With no trash tool, trashing is a permanent delete, so a trash item's base class rises
  from S1 to S2.

### R-4: The protected set is never planned for removal

At any level and scope, the engine refuses to plan these:
- **Branches:** the trunk and release branches (`dev`, `main`, `master`, or as
  configured); the checked-out branch; any branch checked out in a dirty or locked
  worktree; the prefixes `retain/`, `preserve/`, `archive/`.
- **Paths:** tracked files; `.git/`; `.env*`; `*.pem`, `*.key`, `id_*`; `.quest/`;
  `.lore/`; anything under `docs/`; `.pi/`; the `[immaculate] keep` list.
- **Runtime:** containers and images named in `protect.containers` / `protect.images`.
  The built-in entry is the self-hosted CI runner `opum-runner` and its image. Also
  anything labelled `housekeeping.protect=true`; Claude Code itself, editors, language
  servers, and pm2.
- **Harness:** the current session's transcript and scratchpad; plugin versions a live
  session still uses; managed settings.

A protected item may still appear in the report. At Immaculate it gets the automatic
disposition *kept (protected: reason)*. It is never in the plan.

### R-5: A branch with unique commits is unlanded work, not clutter

This is the only irreversible mistake in git housekeeping, so the proof bar is explicit.
A local or remote branch is removable as **landed** only when all of these hold:

1. The remote-tracking refs were fetched with `--prune` in this pass.
2. At least one containment proof holds against the integration branch:
   - ancestry: `git merge-base --is-ancestor <tip> origin/<trunk>`;
   - squash equivalence: the merge-tree of the branch onto the trunk equals the trunk's
     tree;
   - PR state: a `MERGED` PR whose merge commit is an ancestor of `origin/<trunk>`.
3. No dirty or locked worktree has it checked out. A clean worktree is removed first, in
   the same apply.

"Upstream gone" is **not** a containment proof. A branch that fails the proof is
`UNLANDED`. Removing it is S3 and requires an `archive/<name>` ref first.

When `opum-sdlc` is installed, its rules govern branch naming, merge strategy, and
promotion (ADR-0002). This spec only adds the classification and the gate.

### R-6: Apply exactly what was reviewed

Removals go through the engine's plan/apply cycle (ADR-0003):
- `hk plan` writes a plan with a fingerprint per item (SHA, mtime and size, container ID).
- `hk apply` re-checks each fingerprint. It skips any item that changed since planning,
  runs only S3 items whose IDs were confirmed, and appends every action with its undo
  recipe to a journal.
- Engine state (plans, journals, ledger, dispositions) lives under
  `<git-common-dir>/housekeeping/`, never in the working tree: housekeeping must not
  itself leave untracked files behind.
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

### R-8: Every pass reports; Immaculate proves its final state

Every pass ends with a report of:
- the level and scope, and how they were chosen;
- each phase's actions, with class and result;
- skipped items and why;
- bytes reclaimed;
- the journal path for undo;
- open findings outside the scope.

An **Immaculate** pass also verifies:
1. **Disposition.** `hk disposition` lists every in-scope inventory item. Each one needs
   an intentional disposition: *kept* (with the reason), *removed*, *landed*, *deferred*
   (to a named task), or *accepted* (a known, accepted state). Protected and keep-list
   items are disposed automatically as kept. The pass is complete only when nothing is
   unaccounted for (exit 0).
2. **Final-state checks.** The working tree is clean or explained; the branch is pushed;
   the tracker and docs gates pass; and the `[immaculate] verify` commands (for example, a
   from-scratch install, build, and test) exit 0.

The report carries this as the **disposition record**.

## Design

### What each level adds

Cells are cumulative: a level also does everything to its left. The scope column in the
engine filters which of these items a pass may act on.

| Phase | Minimal | Light | Standard (default) | Deep | Immaculate |
|---|---|---|---|---|---|
| **Record** | a progress note on the In Progress task: where things stand and what is next | + update the immediate issue; criteria checked with evidence | + reconcile issue statuses with commits; update relevant docs and handoff notes; close a finished task in its delivering PR; gates: `lore check`, `quest agents --check --target claude`, `lore agents --check`, `quest doctor` (read `data.healthy`) | + outdated status information (stale In Progress tasks, drifted Stories, `lore orphans`, `stale_after`); obsolete documentation; two-way spec-drift reconciliation (fix code, amend spec, or record a deviation) | + every task and document touched has a stated disposition |
| **Land** | preserve the work: commit it (a WIP commit if needed) on the task branch and push | commit completed work in logical units; push | + open or refresh the PR; merge when checks are green; delete the local branch after its merge; promote only on request | | + the branch state is verified (pushed, landed, or deferred) |
| **Clear** | nothing | task-generated temporary files: the ledger's junk (S1), processes and dev servers (S1), clean worktrees (S1), temp (S2) | known disposable artifacts: landed branches, local and remote (S1); prunable worktrees and clean worktrees of landed branches (S1); ignored junk (S1); junk-named untracked files (S2, reviewed); this project's containers: stop (S1), remove when stopped (S2); orphaned processes in the repo (S2) | the places routine housekeeping misses: stale unlanded branches, archived then deleted (S3); other clean worktrees (S1); old stashes, archived then dropped (S1); build outputs and dependency dirs (S2); disposable caches (S2); `$TMPDIR` entries with configured prefixes (S2); old session scratchpads (S2); project images and networks (S2/S1) and volumes (S3); Claude Code debris and bloat proposals (memory, CLAUDE.md, permissions, hooks, plugins) | anything left in scope is either disposed of or explicitly kept: untracked unknown files and non-build ignored files (S3, or kept with a reason) |
| **Verify** | the work is recoverable (committed and pushed, or its location is recorded) | no ledger process alive; no ledger junk left | no landed branch left; gates green | reclaimed bytes measured | `hk disposition` exits 0; `[immaculate] verify` commands exit 0 |

**Machine scope** adds, at Deep and above:
- global dev caches, via their own prune commands (S2);
- all Docker: unused images, stopped containers, build cache (S2), dangling volumes (S3);
- the Claude Code plugin cache: orphaned versions and dead in-use markers (S2);
- transcripts of deleted projects (S3);
- user settings findings;
- other projects' scratchpads (S2);
- orphaned dev processes outside the repo (S3).

### Choosing a level

When the user names a level, use it. Otherwise infer it from context, state it in the
plan, and let the user raise or lower it:

1. Context is about to run out, an emergency stop, "save where we are" → **Minimal**.
2. The session is ending, "wrap up for today", a handoff → **Light**.
3. A bare "clean up" or "tidy up"; a task has just finished, a PR merged, "close this
   out" → **Standard** (the default).
4. "Deep clean", disk space, "things have piled up" → **Deep**.
5. "Immaculate", "spotless", "leave nothing behind"; before a release, a handover to
   another team, or an audit → **Immaculate**.

Scope defaults to `repo`. Use `session` when the user says "just what you did". Use
`machine` only when the user asks about the machine, disk space overall, global caches,
all of Docker, or `~/.claude`. `.housekeeping.toml` may set the defaults. An agent may
always choose a *lower* level or a narrower scope when unsure. Going *higher* or *wider*
than the user asked requires asking.

### Configuration

`.housekeeping.toml` sits at the repository root and is committed. Every key is optional.
The engine's built-in defaults apply without the file.

```toml
version = 1
housekeeping_level = "standard"   # minimal | light | standard | deep | immaculate
housekeeping_scope = "repo"       # session | repo | machine

[levels]                          # context -> level, when the user names none
checkpoint = "minimal"
session_end = "light"
default = "standard"
task_done = "standard"

[sdlc]                            # auto-detected when omitted
trunk = "dev"
release = "main"
merge = "squash"

[protect]                         # extends the built-in protected set
branches = ["retain/*", "preserve/*", "archive/*"]
paths = []
containers = ["opum-runner"]
images = ["*opum-actions-runner*"]

[junk]
patterns = []

[tmp]                             # $TMPDIR entries attributed to this repo
prefixes = []
max_age_days = 2

[stash]
max_age_days = 30

[branches]
stale_days = 30

[provenance]                      # opt-in capture hook
enabled = false

[immaculate]
keep = [".env", ".env.local"]     # disposed as "kept: keep-list"
verify = []                       # e.g. ["npm ci", "npm test"]
```

### The engine and the skills

The skills make judgement calls. The engine (`scripts/hk.py`, stdlib Python 3.9+) does
the deterministic work: inventory, classification, planning, applying, journalling, undo,
and disposition. Commit, PR, merge, and promotion are *landing* operations. The skills
perform them directly under `opum-sdlc`. The engine only probes their state.

| Skill | Phases it owns |
|---|---|
| `tidy` | chooses the level and scope; runs the phases in order; writes the report and, at Immaculate, the disposition record (`/clean <level> [scope]`) |
| `session-sync` | Record |
| `git-hygiene` | Land; the git part of Clear |
| `workspace-clean` | Clear for files, temp, builds, caches |
| `runtime-clean` | Clear for containers, processes, ports, background tasks |
| `harness-hygiene` | Clear and audit for the Claude Code harness |

## Open questions

- **Estate audit.** Should the engine read `sdlc-audit --json` when opum-agent is present
  instead of classifying branches itself? The proposal is to classify natively (it must
  work outside the fleet) and cross-check against `sdlc-audit` when it is available,
  reporting any disagreement.
- **Disposition persistence.** Dispositions live in `.git/housekeeping/dispositions.json`,
  which is machine-local. Should an Immaculate pass also write them into the task's final
  summary, or into a docs record, so a reviewer can see them? The proposal is to put the
  summary on the task and the full record in the PR body.
