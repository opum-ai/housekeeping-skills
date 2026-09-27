---
type: Arc
title: session-sync skill
tags:
  - skills
  - session-sync
summary: Reconcile Quest tasks and lore docs with what the session did, including two-way spec drift, before anything is cleared.
tasks:
  - hs-6
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.154Z
lore_task_status: in-progress
---

# session-sync skill

## Goal

Make the tracker and docs tell the truth about what the session did, before anything is cleared.

## Acceptance criteria

- `skills/session-sync/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at each cleanliness level, C1 to C5, and never runs an S3 action without explicit per-item user confirmation
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-6](../../.quest/tasks/HS-6.json) | session-sync skill: reconcile quest tasks and lore docs with what the session did, including two-way spec drift | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- C1: a progress note on the In Progress task; criteria checked only with evidence.
- C2: update lore docs the session touched; file follow-up tasks; review stashes.
- C3: close the task in the delivering PR with `quest task complete`, citing the PR number
  and CI run id; run `lore check`, `quest agents --check`, `lore agents --check` and
  `quest doctor` (reading `data.healthy`, since it exits 0 when unhealthy).
- C4: two-way spec drift across the epic. Each divergence gets one decision: fix the code,
  amend the spec, or record a deviation. No surveyed SDD tool reconciles in both
  directions; see [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#8-session-closure-and-post-implementation-reconciliation).
- Tracker and docs rules: [R-7](../specs/cleanliness-levels.md#r-7-record-and-land-follow-the-tracker-and-docs-contracts).
