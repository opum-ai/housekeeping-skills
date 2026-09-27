---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: Provenance capture hook
tags:
  - hook
  - provenance
summary: An opt-in, fail-open PostToolUse hook that records what the session creates into the hk ledger.
tasks:
  - hs-10
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.466Z
lore_task_status: in-progress
---

# Provenance capture hook

## Goal

Record what the session creates, cheaply and without ever blocking, so cleanup can prove what it owns.

## Acceptance criteria

- The hook is registered in `hooks/hooks.json` and is a no-op unless `[provenance] enabled = true`
- The hook exits 0 on malformed input, missing config and an unwritable ledger, proven by tests
- `hk inventory` consumes ledger entries as `provenance = ledger`

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-10](../../.quest/tasks/HS-10.json) | Opt-in provenance capture hook (fail-open) feeding the hk ledger | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Design: [ADR-0004](../adr/0004-opt-in-provenance-ledger-via-a-fail-open-capture-hook.md).
- The ledger is gitignored and per session. It records new untracked files, branches,
  worktrees, containers, and background commands with their PIDs.
- The hook never does cleanup itself. A SessionEnd hook has a 1.5 s budget and cannot block
  exit, so cleanup lives in the skills.
