---
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
- The skill states its behaviour at each cleanliness level, C1 to C5, and never runs an S3 action without explicit per-item user confirmation
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-5](../../.quest/tasks/HS-5.json) | git-hygiene skill: stage, commit, push, PR, merge, promote, and prune branches, worktrees, stashes, and refs | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Land: logical commits and push (C1), open or refresh the PR (C2), squash-merge when
  green and promote only on request (C3). Policy comes from `opum-sdlc` when installed
  ([ADR-0002](../adr/0002-defer-branch-pr-and-promotion-policy-to-opum-sdlc.md)).
- Clear: landed branches local and remote, prunable worktrees and stale refs (C3); stale
  unlanded branches archived then deleted, and old stashes exported then dropped (C4).
- A branch is landed only on a proof from
  [R-5](../specs/cleanliness-levels.md#r-5-a-branch-with-unique-commits-is-unlanded-work-not-clutter): ancestry,
  squash equivalence, or a merged PR, after a fresh `fetch --prune`. "Upstream gone" is
  not a proof. This is the rule `/clean_gone` breaks; see [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#1-prior-art-skills-plugins-and-commands).
