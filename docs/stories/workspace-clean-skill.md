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
lore_task_status: done
---

# workspace-clean skill

## Goal

Clear files the work left behind, from this session's junk up to regenerable build outputs and caches, without ever touching local-but-precious files.

## Acceptance criteria

- `skills/workspace-clean/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at the housekeeping levels (Minimal to Immaculate) and scopes (session, repo, machine) it acts at, and never runs an S3 action without explicit user confirmation.
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-7](../../.quest/completed/HS-7.json) | workspace-clean skill: agent junk, temp dirs, build outputs, dependency dirs, and caches | Done |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Light: the ledger's junk files (S1) and task-generated temp (S2).
- Standard: ignored junk (S1); junk-named untracked files (S2, reviewed).
- Deep: build outputs and dependency dirs chosen by ecosystem allowlist, disposable
  project caches, and `$TMPDIR` entries under configured prefixes, all S2.
- Immaculate: every remaining in-scope file is disposed of or explicitly kept. Untracked
  unknown files and non-build ignored files are S3 or kept with a reason; the
  `[immaculate] keep` list (for example `.env`) is kept automatically. This is not a
  fresh-clone reset.
- Machine scope only, at Deep and above: global dev caches through their own prune
  commands (S2).
- Never `git clean -X`, which deletes ignored `.env` files. Never delete by glob or age in
  a shared temp dir; the auto-mode classifier blocks it and it is unsafe. See
  [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#3-files-build-outputs-and-caches).
