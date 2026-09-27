---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: Design of record
tags:
  - design
  - research
summary: The research survey, the housekeeping-levels spec and the ADRs that fix the plugin's design before code lands.
tasks:
  - hs-2
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.623Z
lore_task_status: done
---

# Design of record

## Goal

Fix the plugin's design in reviewed docs before code lands, so every skill and the engine build against one agreed model.

## Acceptance criteria

- `docs/reference` holds a state-of-the-art survey with a source URL on every external claim
- `docs/specs` holds the cleanliness-levels spec defining C1-C5, S0-S3, the protected set and reach per level
- Five ADRs record the ratified decisions: focused skills, deferring to opum-sdlc, the shared engine, the provenance ledger, and graduated reach
- An upstream-findings reference lists each finding with owner, version, repro, exit code and classification
- `lore check` exits 0

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-2](../../.quest/completed/HS-2.json) | Research and design of record: state of the art, cleanliness-level spec, ADRs | Done |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Spec: [Housekeeping levels](../specs/cleanliness-levels.md). Levels Minimal to Immaculate
  and the separate scope setting replaced the C1-C5 draft on 2026-09-27
  ([ADR-0006](../adr/0006-housekeeping-levels-minimal-to-immaculate-with-scope-as-a-separate-setting.md), HS-13).
- Research: [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md) and [Upstream findings](../reference/upstream-findings.md).
- Decisions: ADR-0001 to ADR-0006, listed in the [Epic](../epics/housekeeping-for-agentic-engineering.md#decisions).
- The spec's two open questions (the estate audit and where dispositions persist) stay
  open until the engine story settles them.
