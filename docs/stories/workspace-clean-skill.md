---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: workspace-clean skill
tags:
  - skills
  - workspace-clean
summary: Clear agent junk, attributed temp dirs, build outputs, dependency dirs and caches through the engine, never through git clean -X.
tasks:
  - hs-7
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.232Z
lore_task_status: todo
---

# workspace-clean skill

## Goal

Clear files the work left behind, from this session's junk up to regenerable build outputs and caches, without ever touching local-but-precious files.

## Acceptance criteria

- `skills/workspace-clean/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at each cleanliness level, C1 to C5, and never runs an S3 action without explicit per-item user confirmation
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-7](../../.quest/tasks/HS-7.json) | workspace-clean skill: agent junk, temp dirs, build outputs, dependency dirs, and caches | To Do |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- C2: ledger-owned junk files (S1).
- C4: build outputs and dependency dirs chosen by ecosystem allowlist, project caches,
  `$TMPDIR` entries under configured prefixes, all S2.
- C5: the checkout reset to fresh-clone state minus `[cleanroom] keep` (S2 for ignored
  files, S3 for untracked), and global caches through their official prune commands.
- Never `git clean -X`, which deletes ignored `.env` files. Never delete by glob or age in
  a shared temp dir; the auto-mode classifier blocks it and it is unsafe. See
  [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#3-files-build-outputs-and-caches).
