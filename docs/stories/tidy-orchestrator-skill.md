---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: tidy orchestrator skill
tags:
  - skills
  - tidy
summary: The tidy skill chooses a cleanliness level, runs survey, record, land, clear, verify and report in order, and writes the pass report.
tasks:
  - hs-4
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.000Z
lore_task_status: todo
---

# tidy orchestrator skill

## Goal

One entry point that picks a cleanliness level, runs survey, record, land, clear, verify and report in that order, and hands the user a single report.

## Acceptance criteria

- `skills/tidy/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at each cleanliness level, C1 to C5, and never runs an S3 action without explicit per-item user confirmation
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-4](../../.quest/tasks/HS-4.json) | Orchestrator skill: pick a cleanliness level, run the ladder in order record, land, clear, verify, and report | To Do |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Level choice follows the spec's context rules: session end → C1; a bare "clean up" → C2;
  a finished task → C3; disk pressure → C4; "pristine" or pre-release → C5. The inferred
  level is stated in the plan. Going higher than asked requires asking.
- It calls the domain skills in phase order and holds no domain rules of its own
  ([ADR-0001](../adr/0001-one-plugin-of-focused-skills-plus-a-tidy-orchestrator.md)).
- The report follows [R-8](../specs/cleanliness-levels.md#r-8-every-pass-reports). A C5 pass adds the clean-room
  certificate.
