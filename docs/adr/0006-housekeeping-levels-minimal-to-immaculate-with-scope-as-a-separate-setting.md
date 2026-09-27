---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: Housekeeping levels Minimal to Immaculate, with scope as a separate setting
tags:
  - architecture
  - levels
  - safety
summary: Levels Minimal to Immaculate (default Standard) set how much housekeeping a pass does, a separate scope (session, repo, machine) sets where, and Immaculate verifies rather than purges.
generated:
  by: lore/0.11.0
  at: 2026-09-27T14:03:38.616Z
---

# Housekeeping levels Minimal to Immaculate, with scope as a separate setting

## Status

Accepted (2026-09-27). Decided by the user.

Supersedes the "graduated reach" table in
[ADR-0005](0005-graduated-reach-other-repos-working-trees-are-never-mutated.md), where C4
and C5 widened reach. ADR-0005's core rule stands: other repositories' working trees are
never mutated, at any level or scope.

## Context

The first draft of the design of record had five cleanliness levels: C1 Tidy, C2 Sweep,
C3 Clean, C4 Deep clean and C5 Clean room. That scale had two problems.

- **It tied depth to reach.** Each level also widened where a pass could act
  (ADR-0005). C4 reached the user-level harness and temp. C5 reached global dev caches and
  all of Docker on the machine. A request for a thorough pass in one repo therefore also
  authorized machine-wide deletions. How much to do and where to do it are two separate
  questions, and one dial answered both.
- **It made the top level a purge.** C5 "Clean room" reset the checkout to fresh-clone
  state and proved it rebuilt. That is removing things, not keeping a project in order. A
  project in active use legitimately keeps a `.env`, a `retain/` branch, or a task deferred
  to a follow-up. A purge either deletes these or fails.

The user also ruled on what the plugin is for. It does **project housekeeping**: commits,
branches, worktrees, caches, containers, issue statuses, documentation and handoffs. It
does not improve the code. Formatting, dead code and refactors belong to other tools.

## Decision

Three independent settings govern every pass. They are specified in
[Housekeeping levels](../specs/cleanliness-levels.md).

1. **Level** (`housekeeping_level`) sets *how much* housekeeping to do. There are five
   cumulative levels:

   | Level | Name | Meaning |
   |---|---|---|
   | 1 | **Minimal** | Preserve the work and record where things stand. |
   | 2 | **Light** | Put away what you just used. |
   | 3 | **Standard** (default) | Complete the routine housekeeping checklist. |
   | 4 | **Deep** | Check the places routine housekeeping misses. Resolve what is safe and authorized. |
   | 5 | **Immaculate** | Complete deep housekeeping, then verify the final state. |

2. **Scope** (`housekeeping_scope`: `session | repo | machine`, default `repo`) sets
   *where* a pass may act. A level never widens the scope: deep-cleaning the kitchen does
   not authorize remodeling the house. Machine-wide purges run only at machine scope. These
   are global caches, all of Docker, the plugin cache, and transcripts of deleted
   projects. See
   [R-2](../specs/cleanliness-levels.md#r-2-levels-are-cumulative-scope-is-a-separate-setting).

3. **Safety class** (S0-S3) stays a property of each operation and its evidence. It is
   never set by the level or the scope.

**Immaculate verifies; it does not purge.** The dividing line at the top is "perform the
chores" versus "verify that no applicable chores remain". Every in-scope change, branch,
issue, document and artifact needs an intentional disposition: kept (with the reason),
removed, landed, deferred (to a named task) or accepted. The goal is nothing left
unattended, not nothing left on disk. The report carries this as the disposition record
([R-8](../specs/cleanliness-levels.md#r-8-every-pass-reports-immaculate-proves-its-final-state)).

In the engine, this becomes:
- `hk --level minimal|light|standard|deep|immaculate`, also accepting `1`-`5` and the
  legacy aliases `c1`-`c5`;
- `hk --scope session|repo|machine`;
- `hk disposition`, which exits 0 when nothing in scope is unaccounted for;
- engine state under `.git/housekeeping/`;
- the command `/clean <level> [scope] [audit]`.

Rejected alternatives:
- **The C1-C5 scale** (Tidy, Sweep, Clean, Deep clean, Clean room). It coupled depth to
  reach and made the top level a purge; see Context.
- **Tidy → Light → Standard → Deep → White-Glove.** This was the user's intermediate draft.
  It also mixed in code-improvement chores, which are out of scope for project housekeeping.
- **Other names for the top level:**
  - *Absolute* implies an unconditional guarantee.
  - *Strict* describes how firmly rules are enforced, not how much gets done.
  - *Maximum* does not describe the result.
  - *Pristine* suggests an untouched state.
  - *Sterile* and *clean room* emphasize removing contamination.

  *Immaculate* allows a project to be in active use and completely in order.

## Consequences

- A thorough pass is safe to ask for in one repository. "Deep clean" means a deep pass at
  the configured scope, which is the repo by default. It never reaches global caches or
  machine-wide Docker unless machine scope was asked for.
- What the C1-C5 draft placed at C4 or C5 because it lay outside the repo now needs Deep
  (or Immaculate) *and* machine scope. Examples are global caches, all of Docker, the plugin
  cache and deleted-project transcripts. Project-scoped items keep their level: project
  images, networks and volumes are Deep at repo scope.
- Other repositories' working trees are still never mutated, at any level or scope
  ([ADR-0005](0005-graduated-reach-other-repos-working-trees-are-never-mutated.md)).
  Machine scope reports them.
- Immaculate has a verifiable exit condition: `hk disposition` exits 0, and the
  `[immaculate] verify` commands exit 0. A kept `.env` or a deferred task does not block it.
  The C5 fresh-clone reset and its `[cleanroom] keep` list are gone; the `[immaculate] keep`
  list now marks items as kept.
- The skills, the `/clean` command, the README, the example `.housekeeping.toml` and the
  engine all move to the new names in HS-13. The `c1`-`c5` aliases stay accepted, so
  existing invocations keep working.
- ADR-0001 to ADR-0005 keep their C1-C5 wording as history.
