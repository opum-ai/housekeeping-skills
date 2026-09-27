---
type: Arc
title: Skill evaluation suite
tags:
  - evals
summary: Fixtures, with-skill and without-skill task evals, trigger sets and safety cases that prove the skills are useful and never destroy unlanded work.
tasks:
  - hs-11
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.544Z
lore_task_status: in-progress
---

# Skill evaluation suite

## Goal

Prove each skill improves outcomes over no skill, triggers on the right requests, and never destroys unlanded work.

## Acceptance criteria

- `evals/evals.json` lists every task eval with assertions
- Objective graders check the resulting repo and filesystem state rather than the agent's report
- `benchmark.json` and `benchmark.md` exist for at least one iteration comparing with-skill and without-skill
- Each skill has a trigger set with at least 5 should-fire and 3 near-miss queries

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-11](../../.quest/tasks/HS-11.json) | Evaluation suite: fixtures, task evals with and without skills, trigger sets, benchmark | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Fixtures: a bare remote; branches in every containment state (merged, squash-merged,
  unlanded, gone-but-unmerged, `retain/`, checked out in a dirty worktree); junk and build
  files; a fake HOME with `~/.claude` debris.
- Safety cases fail any run that deletes an unlanded branch, a dirty worktree, a `.env`
  file, or a protected container.
