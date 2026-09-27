---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
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
- The skill states its behaviour at the housekeeping levels (Minimal to Immaculate) and scopes (session, repo, machine) it acts at, and never runs an S3 action without explicit user confirmation.
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-6](../../.quest/tasks/HS-6.json) | session-sync skill: reconcile quest tasks and lore docs with what the session did, including two-way spec drift | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Minimal: a progress note on the In Progress task: where things stand and what is next.
- Light: update the immediate issue; criteria checked only with evidence.
- Standard: reconcile issue statuses with commits; update relevant docs and handoff notes;
  close a finished task in the delivering PR with `quest task complete`, citing the PR
  number and CI run id; run `lore check`, `quest agents --check`, `lore agents --check` and
  `quest doctor` (reading `data.healthy`, since it exits 0 when unhealthy).
- Deep: outdated status information (stale In Progress tasks, drifted Stories,
  `lore orphans`, `stale_after`); obsolete documentation; two-way spec drift across the
  epic. Each divergence gets one decision: fix the code, amend the spec, or record a
  deviation. No surveyed SDD tool reconciles in both directions; see [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#8-session-closure-and-post-implementation-reconciliation).
- Immaculate: every task and document touched has a stated disposition; anything deferred
  names its follow-up task.
- Tracker and docs rules: [R-7](../specs/cleanliness-levels.md#r-7-record-and-land-follow-the-tracker-and-docs-contracts).
