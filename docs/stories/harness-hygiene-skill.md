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
lore_task_status: in-progress
---

# harness-hygiene skill

## Goal

Audit and clear the Claude Code harness debris that the built-in retention sweep leaves behind, using the built-in commands wherever they exist.

## Acceptance criteria

- `skills/harness-hygiene/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at the housekeeping levels (Minimal to Immaculate) and scopes (session, repo, machine) it acts at, and never runs an S3 action without explicit user confirmation.
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-9](../../.quest/tasks/HS-9.json) | harness-hygiene skill: Claude Code sessions, transcripts, memory, CLAUDE.md, plugins, hooks, permissions, MCP, worktrees | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- S0 probes: `claude doctor`, `claude plugin list`, `claude plugin details <name>` for
  context cost. `/doctor` is user-invoked, so the skill recommends it rather than runs it.
- Deep, at repo scope, clears this project's old session scratchpads (S2) and proposes,
  applied only on approval: memory, CLAUDE.md, permission, hook and plugin hygiene.
- Machine scope only, at Deep and above: orphaned plugin-cache versions and dead in-use
  markers (S2); other projects' scratchpads (S2); transcripts of deleted project paths via
  `claude project purge --dry-run` first (S3); user settings findings.
- Never the current session's transcript or scratchpad, or managed settings.
- What `cleanupPeriodDays` does and does not sweep is summarised in
  [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#5-claude-codes-built-in-hygiene-surface).
