---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: tidy orchestrator skill
tags:
  - skills
  - tidy
summary: The tidy skill chooses a housekeeping level and scope, runs survey, record, land, clear, verify and report in order, and writes the pass report.
tasks:
  - hs-4
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.000Z
lore_task_status: in-progress
---

# tidy orchestrator skill

## Goal

One entry point that picks a housekeeping level and scope, runs survey, record, land, clear, verify and report in that order, and hands the user a single report.

## Acceptance criteria

- `skills/tidy/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at the housekeeping levels (Minimal to Immaculate) and scopes (session, repo, machine) it acts at, and never runs an S3 action without explicit user confirmation.
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-4](../../.quest/tasks/HS-4.json) | Orchestrator skill: pick a housekeeping level and scope, run record, land, clear, verify, and report | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Level choice follows the spec's [context rules](../specs/cleanliness-levels.md#choosing-a-level):
  context running out or "save where we are" → Minimal; session end or a handoff → Light;
  a bare "clean up", a finished task or a merged PR → Standard (the default); "deep clean"
  or piled-up debris → Deep; "immaculate", pre-release, a handover or an audit → Immaculate.
- Scope is chosen separately and defaults to `repo`: `session` for "just what you did",
  `machine` only when the user asks about the machine, global caches, all of Docker or
  `~/.claude`. A level never widens the scope
  ([ADR-0006](../adr/0006-housekeeping-levels-minimal-to-immaculate-with-scope-as-a-separate-setting.md)).
- The inferred level and scope are stated in the plan. Going higher or wider than asked
  requires asking; going lower or narrower does not.
- The user entry point is `/clean <level> [scope] [audit]`; `audit` gives a read-only plan.
- It calls the domain skills in phase order and holds no domain rules of its own
  ([ADR-0001](../adr/0001-one-plugin-of-focused-skills-plus-a-tidy-orchestrator.md)).
- The report follows [R-8](../specs/cleanliness-levels.md#r-8-every-pass-reports-immaculate-proves-its-final-state).
  An Immaculate pass adds the disposition record: `hk disposition` exits 0 (every in-scope
  item is kept, removed, landed, deferred or accepted) and the `[immaculate] verify`
  commands exit 0.
