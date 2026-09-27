---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: One plugin of focused skills plus a tidy orchestrator
tags:
  - architecture
  - skills
summary: "Five focused domain skills plus a tidy orchestrator that picks the level and runs the phases in order, in one plugin, instead of one monolithic housekeeping skill."
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:18.761Z
---

# One plugin of focused skills plus a tidy orchestrator

## Status

Accepted (2026-09-26). Decided by the user.

## Context

Housekeeping spans six domains that share little code but share one safety model:
- recording progress in the tracker and docs;
- landing work through git and the forge;
- files, temp dirs, build outputs and caches;
- containers and processes;
- the Claude Code harness itself;
- choosing how far to go, and in what order.

The prior art splits the same way, and none of it covers all six. commit-commands covers
commits and branch pruning. superpowers covers finishing one branch. cctop covers ports.
claude-code-cleaner covers `~/.claude`. See
[State of the art, section 1](../reference/state-of-the-art-in-agentic-housekeeping.md#1-prior-art-skills-plugins-and-commands).

Three constraints shape how the work is packaged:
- **Context cost.** Every skill description sits in context on every turn. A single skill
  covering six domains needs a long description and a body that is mostly irrelevant to
  any one request.
- **Triggering.** "Prune my branches" and "free some disk" are different requests. A
  focused description triggers on the right one. A monolithic one triggers on everything
  or nothing.
- **Ordering.** Clearing can destroy the evidence recording needs. Something has to run
  the phases in a fixed order: record, land, clear, verify, report.

## Decision

Ship one plugin, `housekeeping-skills`, holding six skills:

| Skill | Owns |
|---|---|
| `tidy` | Chooses the level; runs the phases in order; writes the report |
| `session-sync` | Record |
| `git-hygiene` | Land; the git part of Clear |
| `workspace-clean` | Clear for files, temp, builds and caches |
| `runtime-clean` | Clear for containers, processes, ports and background tasks |
| `harness-hygiene` | Clear and audit for the Claude Code harness |

Each domain skill can run alone at any level. `tidy` composes them for a whole pass. All
six drive the same engine (ADR-0003) and read the same
[cleanliness-levels spec](../specs/cleanliness-levels.md).

Rejected alternatives:
- **One monolithic `housekeeping` skill.** One description would carry every trigger, and
  one body every domain's rules. It would also force every request through the full
  ladder, even "just commit this".
- **Separate plugins per domain.** Six installs, six versions, and no shared engine or
  config. The safety model would drift between them.
- **Domain skills with no orchestrator.** The user or agent would have to remember the
  phase order. Clearing before recording destroys the logs, scratch output and dirty
  worktrees a record needs, and clearing before landing deletes branches that were never
  merged
  ([R-1](../specs/cleanliness-levels.md#r-1-durable-before-disposable)).

## Consequences

- Each skill description stays short and specific. Near-miss trigger sets can test them
  separately (HS-11).
- The orchestrator is thin. It picks a level, calls the domain skills in phase order, and
  merges their reports. It holds no domain rules of its own.
- Domain skills must not assume `tidy` ran first. Each one surveys before it acts.
- One plugin version covers all six skills, so a fix to the shared engine ships to all of
  them at once.
