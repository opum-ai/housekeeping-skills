---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: git-hygiene skill
tags:
  - skills
  - git-hygiene
summary: Land work under opum-sdlc or the fallback, then prune landed branches, worktrees, stashes and refs using containment proofs rather than upstream-gone.
tasks:
  - hs-5
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.078Z
lore_task_status: in-progress
---

# git-hygiene skill

## Goal

Land the session's work under the repository's SDLC, then prune only what containment proofs show is landed.

## Acceptance criteria

- `skills/git-hygiene/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at the housekeeping levels (Minimal to Immaculate) and scopes (session, repo, machine) it acts at, and never runs an S3 action without explicit user confirmation.
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-5](../../.quest/tasks/HS-5.json) | git-hygiene skill: stage, commit, push, PR, merge, promote, and prune branches, worktrees, stashes, and refs | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Land: preserve the work with a commit (WIP if needed) on the task branch and push
  (Minimal); commit completed work in logical units and push (Light); open or refresh the
  PR, merge when checks are green, delete the local branch after its merge, and promote
  only on request (Standard); verify every branch is pushed, landed or deferred
  (Immaculate). Policy comes from `opum-sdlc` when installed
  ([ADR-0002](../adr/0002-defer-branch-pr-and-promotion-policy-to-opum-sdlc.md)).
- Clear: this session's clean worktrees (Light, S1); landed branches local and remote,
  prunable worktrees and clean worktrees of landed branches (Standard, S1); stale unlanded
  branches archived then deleted (Deep, S3), other clean worktrees and old stashes archived
  then dropped (Deep, S1).
- All of this is repo-scoped. Other repositories' branches and worktrees are reported,
  never mutated, at any level or scope
  ([ADR-0005](../adr/0005-graduated-reach-other-repos-working-trees-are-never-mutated.md)).
- A branch is landed only on a proof from
  [R-5](../specs/cleanliness-levels.md#r-5-a-branch-with-unique-commits-is-unlanded-work-not-clutter): ancestry,
  squash equivalence, or a merged PR, after a fresh `fetch --prune`. "Upstream gone" is
  not a proof. This is the rule `/clean_gone` breaks; see [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#1-prior-art-skills-plugins-and-commands).
