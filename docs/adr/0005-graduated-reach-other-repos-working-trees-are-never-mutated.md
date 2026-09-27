---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: "Graduated reach: other repos' working trees are never mutated"
tags:
  - architecture
  - safety
summary: Each level widens what a pass may mutate, but no level, not even C5, mutates another repository's working tree; other repos are reported to their own sessions.
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:19.072Z
---

# Graduated reach: other repos' working trees are never mutated

## Status

Accepted (2026-09-26). Decided by the user.

## Context

A deep clean is tempting to run machine-wide. The measured debris on one machine was
spread across 65 repository directories, the harness, `$TMPDIR` and Docker. See
[State of the art, section 10](../reference/state-of-the-art-in-agentic-housekeeping.md#10-measured-machine-inventory-snapshot-2026-09-26).
Other repos held worktrees, handover markers and scratch files.

Three facts argue against touching them:
- **One session owns each repo.** The fleet operating model runs one live session per
  repository. `opum-sdlc` says never to checkout, pull, stash, reset or switch in a
  sibling's working directory. Moving another repo's `HEAD`, index or tree without its
  session seeing it is how commits race onto the wrong branch.
- **Unowned deletions are what the classifier blocks.** Auto mode blocks tearing down
  resources Claude did not create in the session, unless the user named them.
- **Tools that ignore ownership cause harm.** Cursor's worktree cleanup deletes worktrees
  it did not create. superpowers' rule is the opposite: "The host environment owns this
  workspace — leave it in place."

At the same time, some cleanup is legitimately machine-scoped: global caches, machine-wide
Docker, the user-level harness.

## Decision

Each level has a **reach**: the set of places it may mutate. Reach widens with the level
([R-2](../specs/cleanliness-levels.md#r-2-levels-are-cumulative-and-scoped-by-reach)):

| Level | Adds to reach |
|---|---|
| C1 | The current repo's index, branch and tracker; the remote task branch |
| C2 | Untracked files and processes this session created |
| C3 | The repo's branches, worktrees and refs; this project's stopped containers |
| C4 | The repo's ignored outputs and caches; this project's images, networks and volumes; the user-level harness and attributed temp entries |
| C5 | Global dev caches and machine-wide Docker, minus the protected set; the checkout reset to fresh-clone state |

**Other repositories' working trees are outside reach at every level, including C5.** A
pass reports their state as findings. Their own sessions clean them.

Rejected alternatives:
- **Letting C5 reach every repo.** It would race live sessions in those repos, and it
  would make C5 unsafe to run while any other session is open.
- **A flat reach with per-item confirmation.** Confirmation fatigue turns into "yes to
  all", which the S3 rule forbids.
- **Reporting only, even for machine-wide caches.** Global caches and Docker are
  regenerable and have official prune commands. Refusing them would leave the largest
  piles untouched.

## Consequences

- C5 is safe to run while other sessions are live. It never moves another repo's `HEAD`.
- Debris in other repos, such as `.claude/handovers/` markers or linked worktrees, shows
  up in the report with the owning repo named. The fix belongs there, or upstream; see
  [Upstream findings](../reference/upstream-findings.md).
- Machine-wide operations at C5 still honour the protected set, including a self-hosted
  CI runner in any Docker context.
- Reach is enforced by the engine, not by the skill's prose, so a mis-scoped plan fails
  before it is shown.
