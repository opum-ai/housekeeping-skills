---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: A shared stdlib plan-apply engine with fingerprinted plans, a journal and undo
tags:
  - architecture
  - engine
  - safety
summary: "All removals go through hk, a stdlib-Python engine that fingerprints each planned item, re-checks it at apply time, and journals every action with an undo recipe."
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:18.916Z
---

# A shared stdlib plan-apply engine with fingerprinted plans, a journal and undo

## Status

Accepted (2026-09-26). Decided by the user.

## Context

Most agent cleanup today is prose instructions plus shell the model writes on the spot.
The research shows where that fails:
- **Incidents.** Several `rm -rf $HOME` reports came from cleanup code whose target was a
  variable, expanded late, inside a script the permission check could not see into
  (anthropics/claude-code#93099, #88462). See
  [State of the art, section 7](../reference/state-of-the-art-in-agentic-housekeeping.md#7-agent-incidents-during-cleanup).
- **The classifier.** Auto mode blocks deletion by glob or age in shared temp dirs,
  `rm -rf "$VAR"` with an unseen value, and `git clean -fd`. Ad-hoc shell hits these
  blocks, or, worse, gets through with an unresolved target.
- **No undo.** Checkpoints do not track files changed by Bash, so `/rewind` cannot restore
  a deletion.
- **Drift between review and action.** An agent shows a list, the user approves, and the
  script then acts on a fresh glob that no longer matches the list.

The prior art has the parts but no one combines them. Terraform applies "exactly" a
saved plan. git-town and Aider offer undo. Codex snapshots before deleting. kondo and
npkill dry-run first.

## Decision

All removals go through `hk` (`scripts/hk.py`), a deterministic engine in stdlib-only
Python 3.9+:

- **`hk inventory`** collects candidates from git, files, runtime, harness and caches.
- **`hk plan`** classifies each item by safety class, provenance and protection, and
  writes a plan. Each item carries a **fingerprint**: a SHA for refs, mtime and size for
  files, an ID for containers.
- **`hk apply`** re-checks every fingerprint and skips any item that changed. It runs S3
  items only when their IDs were confirmed one by one. It moves files to trash by default.
- **A journal** records every action with its undo recipe, for example
  `git branch <name> <sha>`.
- **`hk undo`** replays the recipes.
- Every command emits the `{schemaVersion, kind, data}` JSON envelope with semantic exit
  codes, like quest and lore.

The skills make judgement calls; the engine makes no deletions they did not plan. A
skill never deletes through a generated script, never runs `rm -rf "$VAR"` on an
unresolved path, and never defaults to `git clean -X`
([R-6](../specs/cleanliness-levels.md#r-6-apply-exactly-what-was-reviewed)).

Rejected alternatives:
- **Prose plus ad-hoc shell.** This is the pattern behind the incidents, and the one the
  classifier is built to block.
- **Wrapping each domain's own tool** (git-trim, kondo, docker prune) with no shared plan.
  Each tool has its own dry-run format and none has a journal, so there would be no single
  review and no undo.
- **A Node or Rust engine.** Python 3.9+ is present on every supported machine with no
  install step. A compiled binary per platform is the packaging cost the research
  measured at about 620 MB per version for another plugin.

## Consequences

- Every deletion is literal, named, reviewed, re-checked and undoable where the class
  allows. That is also what the auto-mode classifier approves.
- The engine is the one place the protected set, the reach rules and the evidence rules
  are enforced, so they are tested once (HS-3) rather than in six skills.
- The engine needs its own tests for every classification boundary, including the
  branch states in R-5.
- Landing (commit, push, PR, merge) stays outside the engine
  ([ADR-0002](0002-defer-branch-pr-and-promotion-policy-to-opum-sdlc.md)).
