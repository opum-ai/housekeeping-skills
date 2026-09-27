---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: harness-hygiene skill
tags:
  - skills
  - harness-hygiene
summary: "Audit and clear Claude Code harness debris: transcripts of deleted projects, scratchpads, orphaned plugin versions, memory, CLAUDE.md, hooks, permissions and MCP."
tasks:
  - hs-9
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.388Z
lore_task_status: todo
---

# harness-hygiene skill

## Goal

Audit and clear the Claude Code harness debris that the built-in retention sweep leaves behind, using the built-in commands wherever they exist.

## Acceptance criteria

- `skills/harness-hygiene/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at each cleanliness level, C1 to C5, and never runs an S3 action without explicit per-item user confirmation
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-9](../../.quest/tasks/HS-9.json) | harness-hygiene skill: Claude Code sessions, transcripts, memory, CLAUDE.md, plugins, hooks, permissions, MCP, worktrees | To Do |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- S0 probes: `claude doctor`, `claude plugin list`, `claude plugin details <name>` for
  context cost. `/doctor` is user-invoked, so the skill recommends it rather than runs it.
- C4 clears: old session scratchpads and orphaned plugin-cache versions (S2); transcripts
  of deleted project paths via `claude project purge --dry-run` first (S3).
- C4 proposes, applied only on approval: memory, CLAUDE.md, permission and hook hygiene.
- Never the current session's transcript or scratchpad, or managed settings.
- What `cleanupPeriodDays` does and does not sweep is summarised in
  [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#5-claude-codes-built-in-hygiene-surface).
