---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: hk plan-apply engine
tags:
  - engine
  - skills
summary: "The stdlib-Python hk engine: inventory, provenance-aware classification, fingerprinted plans, apply with re-checks, a journal, and undo."
tasks:
  - hs-3
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:31.922Z
lore_task_status: todo
---

# hk plan-apply engine

## Goal

Give every skill one deterministic engine for inventory, classification, planning, applying, journalling and undo, so no skill ever deletes through ad-hoc shell.

## Acceptance criteria

- `hk inventory`, `plan`, `apply`, `undo`, `ledger` and `doctor` exist and emit the `{schemaVersion, kind, data}` JSON envelope with semantic exit codes
- `apply` refuses any item whose fingerprint changed since planning, and never executes an S3 item without an explicit per-item confirmation id
- Branch classification never marks a branch with unique unlanded commits as removable, proven by a unit test covering squash-merged, merged, unlanded, gone-but-unmerged, `retain/` and worktree-checked-out branches
- File removal moves to trash by default, refuses paths outside the declared root, and never touches `.env*` or tracked files, proven by unit tests
- The pytest suite passes on Python 3.9

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-3](../../.quest/tasks/HS-3.json) | hk engine: inventory, classify, plan, apply, journal, undo (stdlib Python 3.9+) | To Do |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Design: [ADR-0003](../adr/0003-a-shared-stdlib-plan-apply-engine-with-fingerprinted-plans-a-journal-and-undo.md); rules R-3 to R-6 of the [spec](../specs/cleanliness-levels.md).
- Collectors cover git, files, runtime, harness and caches. Provenance comes from the ledger
  ([ADR-0004](../adr/0004-opt-in-provenance-ledger-via-a-fail-open-capture-hook.md)) or attribution; `unknown` raises the class by one.
- The engine enforces the protected set and each level's reach ([ADR-0005](../adr/0005-graduated-reach-other-repos-working-trees-are-never-mutated.md)).
- It probes landing state but never commits, pushes, merges or promotes ([ADR-0002](../adr/0002-defer-branch-pr-and-promotion-policy-to-opum-sdlc.md)).
