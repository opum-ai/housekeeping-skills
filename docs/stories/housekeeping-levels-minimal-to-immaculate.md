---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: Housekeeping levels Minimal to Immaculate
tags:
  - levels
  - design
  - engine
summary: Adopt the Minimal to Immaculate housekeeping levels with a separate scope setting across the spec, the engine, the skills and the /clean command.
tasks:
  - hs-13
generated:
  by: lore/0.11.0
  at: 2026-09-27T14:06:12.178Z
lore_task_status: done
---

# Housekeeping levels Minimal to Immaculate

## Goal

Replace the C1-C5 draft levels with Minimal, Light, Standard (default), Deep and Immaculate, and make scope a separate setting, everywhere the plugin names a level.

## Acceptance criteria

- The docs spec and an ADR define the five levels, the scope axis, and Immaculate as verified disposition
- `hk` accepts `--level minimal|light|standard|deep|immaculate` and `--scope session|repo|machine`, and plans no machine-scope item unless scope is `machine`, proven by a unit test
- Every skill, the `/clean` command, the README and the `.housekeeping` example use the new names; no C1-C5 names remain outside history
- An Immaculate pass produces a disposition for every in-scope inventory item

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-13](../../.quest/completed/HS-13.json) | Adopt Minimal..Immaculate housekeeping levels with a separate scope axis | Done |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Spec: [Housekeeping levels](../specs/cleanliness-levels.md). Decision:
  [ADR-0006](../adr/0006-housekeeping-levels-minimal-to-immaculate-with-scope-as-a-separate-setting.md).
- It is project housekeeping, not code improvement. A level never widens the scope;
  machine-wide purges run only at `machine` scope
  ([R-2](../specs/cleanliness-levels.md#r-2-levels-are-cumulative-scope-is-a-separate-setting)).
- Immaculate means nothing left unattended, not nothing left on disk: `hk disposition`
  exits 0 when every in-scope item is kept, removed, landed, deferred or accepted
  ([R-8](../specs/cleanliness-levels.md#r-8-every-pass-reports-immaculate-proves-its-final-state)).
- `hk` keeps `1`-`5` and the legacy `c1`-`c5` as level aliases.
