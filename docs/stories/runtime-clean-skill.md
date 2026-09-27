---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: runtime-clean skill
tags:
  - skills
  - runtime-clean
summary: Clear this project's containers, images, networks and volumes, orphaned processes, ports and background tasks, with the protected runtime set excluded.
tasks:
  - hs-8
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.310Z
lore_task_status: in-progress
---

# runtime-clean skill

## Goal

Stop and remove the processes, servers and containers the work started, without touching anyone else's.

## Acceptance criteria

- `skills/runtime-clean/SKILL.md` exists with a name and a trigger-oriented description, under 500 lines
- The skill states its behaviour at the housekeeping levels (Minimal to Immaculate) and scopes (session, repo, machine) it acts at, and never runs an S3 action without explicit user confirmation.
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-8](../../.quest/tasks/HS-8.json) | runtime-clean skill: containers, images, volumes, networks, orphaned processes, ports, background tasks | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Light: processes and dev servers the ledger says this session started (S1).
- Standard: this project's containers, stopped (S1) and removed once stopped (S2);
  orphaned processes in the repo (S2).
- Deep: this project's images (S2), networks (S1) and volumes (S3).
- Machine scope only, at Deep and above: all Docker minus the protected set (unused
  images, stopped containers and build cache S2; dangling volumes S3); orphaned dev
  processes outside the repo (S3).
- The protected runtime set includes the self-hosted CI runner `opum-runner` and its image
  in every Docker context, and anything labelled `housekeeping.protect=true`.
- Scope by Compose label or working directory; SIGTERM before SIGKILL. See
  [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#4-containers-and-processes).
