---
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
- The skill states its behaviour at each cleanliness level, C1 to C5, and never runs an S3 action without explicit per-item user confirmation
- skill-creator eval runs with and without the skill are recorded under `evals/` with graded assertions

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-8](../../.quest/tasks/HS-8.json) | runtime-clean skill: containers, images, volumes, networks, orphaned processes, ports, background tasks | In Progress |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- C2: processes and dev servers the ledger says this session started (S1).
- C3: this project's stopped containers (S1); orphaned processes attributed to the repo
  (S1, or S3 when unattributed).
- C4: this project's images and networks (S2) and volumes (S3).
- C5: machine-wide Docker prune minus the protected set (S2; volumes S3); remaining
  orphaned processes (S3).
- The protected runtime set includes the self-hosted CI runner `opum-runner` and its image
  in every Docker context, and anything labelled `housekeeping.protect=true`.
- Scope by Compose label or working directory; SIGTERM before SIGKILL. See
  [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md#4-containers-and-processes).
