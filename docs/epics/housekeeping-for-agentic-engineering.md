---
# yaml-language-server: $schema=../../.lore/schemas/epic.schema.json
type: Epic
title: Housekeeping for agentic engineering
tags:
  - housekeeping
  - skills
summary: A Claude Code plugin of cleanliness-level housekeeping skills that record, land, clear and verify what agent sessions leave behind, with every removal classed, planned, journalled and undoable.
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:19.149Z
---

# Housekeeping for agentic engineering

## Goal

Leave every agent session's surroundings as clean as the user asked for, and never lose
work doing it.

Coding agents leave debris faster than people do, and most of it is outside the repo. On
one surveyed machine, three weeks of agent work left 25 GB of session scratchpads, 24 GB of
leaked test temp dirs, 1.76 GB of orphaned plugin versions, and 16 orphaned server
processes. See [State of the art](../reference/state-of-the-art-in-agentic-housekeeping.md).
Meanwhile the existing agent tools prune branches on "upstream gone" alone, and the worst
agent incidents on record happened during cleanup.

The plugin delivers three things:
1. **A leveled pass.** Five cumulative levels, from C1 Tidy (record and land this
   session's work) to C5 Clean room (fresh-clone state, proven to rebuild). The user picks
   how far to go, or the orchestrator infers it and says so.
2. **A per-operation gate.** Every operation carries a safety class, S0 Observe to S3
   Irreversible. Evidence only raises it. S3 is confirmed per item, by name, at every level.
3. **One engine for every removal.** Plans are fingerprinted, applied exactly as reviewed,
   journalled, and undoable.

The design of record is the [cleanliness-levels spec](../specs/cleanliness-levels.md).

## Scope

In scope for 0.1.0:
- **Record.** Tracker notes, evidence-backed acceptance criteria, lore docs, and two-way
  spec drift (`session-sync`).
- **Land.** Commits, push, PR, merge and promotion under `opum-sdlc` or a generic fallback,
  then landed-branch, worktree, stash and ref pruning (`git-hygiene`).
- **Clear.** Agent junk, attributed temp dirs, build outputs, dependency dirs and caches
  (`workspace-clean`); containers, images, volumes, processes, ports and background tasks
  (`runtime-clean`); the Claude Code harness (`harness-hygiene`).
- **Orchestrate.** Level choice, phase order, verification and the report (`tidy`).
- **The `hk` engine**, stdlib Python 3.9+.
- **An opt-in provenance hook** that feeds the engine's ledger.
- **Evaluation.** Fixture repos, with-skill and without-skill runs, trigger sets and safety
  cases.

Out of scope for 0.1.0:
- Mutating another repository's working tree, at any level (ADR-0005).
- Scheduled or unattended runs. Destructive passes are user-invoked.
- Hosted dashboards and fleet-wide sweeps. The fleet's own `sdlc-audit` covers estate
  audits.
- Fixing other tools' leaks at their source. Those go to their owners as
  [upstream findings](../reference/upstream-findings.md).

## Design principles

1. **Durable before disposable.** Record, then land, then clear. An interrupted pass
   leaves the durable half done.
2. **The level sets reach; the class sets the gate.** A higher level never makes an
   irreversible operation less gated.
3. **Unique commits are unlanded work, not clutter.** Only a containment proof makes a
   branch removable.
4. **Literal targets only.** Every removal names a resolved, containment-checked item.
   Nothing is deleted by glob, age filter, unresolved variable or generated script.
5. **Defer to the owner.** `opum-sdlc` owns branch policy. Claude Code owns its worktrees and
   transcripts. Another repo's session owns that repo.
6. **Every pass reports.** Level, actions, skips, bytes reclaimed, the journal path, and
   findings outside reach.

## Stories

- [Design of record](../stories/design-of-record.md)
- [hk plan-apply engine](../stories/hk-plan-apply-engine.md)
- [tidy orchestrator skill](../stories/tidy-orchestrator-skill.md)
- [git-hygiene skill](../stories/git-hygiene-skill.md)
- [session-sync skill](../stories/session-sync-skill.md)
- [workspace-clean skill](../stories/workspace-clean-skill.md)
- [runtime-clean skill](../stories/runtime-clean-skill.md)
- [harness-hygiene skill](../stories/harness-hygiene-skill.md)
- [Provenance capture hook](../stories/provenance-capture-hook.md)
- [Skill evaluation suite](../stories/skill-evaluation-suite.md)
- [Plugin packaging](../stories/plugin-packaging.md)

## Decisions

- [ADR-0001 One plugin of focused skills plus a tidy orchestrator](../adr/0001-one-plugin-of-focused-skills-plus-a-tidy-orchestrator.md)
- [ADR-0002 Defer branch, PR and promotion policy to opum-sdlc](../adr/0002-defer-branch-pr-and-promotion-policy-to-opum-sdlc.md)
- [ADR-0003 A shared stdlib plan-apply engine](../adr/0003-a-shared-stdlib-plan-apply-engine-with-fingerprinted-plans-a-journal-and-undo.md)
- [ADR-0004 Opt-in provenance ledger via a fail-open capture hook](../adr/0004-opt-in-provenance-ledger-via-a-fail-open-capture-hook.md)
- [ADR-0005 Graduated reach](../adr/0005-graduated-reach-other-repos-working-trees-are-never-mutated.md)

## Research

- [State of the art in agentic housekeeping](../reference/state-of-the-art-in-agentic-housekeeping.md)
- [Upstream findings](../reference/upstream-findings.md)
