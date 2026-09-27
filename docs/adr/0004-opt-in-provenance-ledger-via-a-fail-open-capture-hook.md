---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: Opt-in provenance ledger via a fail-open capture hook
tags:
  - architecture
  - provenance
  - safety
summary: An opt-in PostToolUse hook records what the session creates into a ledger; it never blocks and fails open. Without it the engine falls back to attribution, and unknown items are raised a safety class.
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:18.994Z
---

# Opt-in provenance ledger via a fail-open capture hook

## Status

Accepted (2026-09-26). Decided by the user.

## Context

Whether an item is safe to remove often depends on who created it. A junk-looking
`debug_v2.log` is disposable if this session wrote it, and someone's work if it was
there before. The same holds for a dev server on port 3000, a worktree, or a container.

The evidence:
- Auto mode allows "deleting the exact jobs Claude created earlier in the same session",
  and blocks tearing down "a stateful resource Claude didn't create in the session".
  Provenance changes what is permitted.
- Port-based process cleanup hooks "kill user-started processes (false positives)"
  (anthropics/claude-code#43944).
- Claude Code's own worktree sweep keeps any worktree without its provenance marker.
  Before that marker existed, the sweep "could remove a worktree you created yourself".
- No surveyed tool keeps a ledger of what an agent session created. See
  [State of the art, section 11](../reference/state-of-the-art-in-agentic-housekeeping.md#11-commodity-and-novel).

Inference alone can attribute some items: Compose labels, a process's working directory,
a configured temp prefix. It cannot tell a file this session wrote from one a person left.

Hooks have limits. A SessionEnd hook "can't block session termination", with a 1.5 s
timeout that plugin hooks cannot raise. A hook that fails loudly on every tool call would
break the session it is meant to serve.

## Decision

- **An opt-in PostToolUse hook** records what the session creates into a gitignored,
  per-session ledger: new untracked files, branches, worktrees, containers, and background
  commands with their PIDs.
- **Off by default.** It runs only when `.housekeeping.toml` sets
  `[provenance] enabled = true`.
- **Fail-open.** It exits 0 on every failure path: malformed input, missing config, an
  unwritable ledger. It never blocks a tool call.
- **Cheap.** It appends a line. It does no inventory and no cleanup.
- `hk inventory` reads the ledger and marks matching items `provenance = ledger`. Items it
  cannot match fall back to `attributed` or `unknown`
  ([R-3](../specs/cleanliness-levels.md#r-3-every-operation-carries-a-safety-class)).

Rejected alternatives:
- **Inference only.** It works for containers and processes with good labels. It fails for
  the most common agent junk: loose files at the repo root.
- **Always-on capture.** It adds a hook to every tool call for every user, including those
  who never run housekeeping. The user asked for opt-in.
- **A fail-closed hook.** A capture bug would block the user's real work. Missing
  provenance is safe, because the engine then raises the item's class.
- **Doing the cleanup in SessionEnd.** 1.5 s is too short, and the hook cannot block exit.

## Consequences

- Without the hook, housekeeping still works. It is just more conservative: an `unknown`
  item is raised one class, so a junk-looking file the session did not record is S3
  unless git ignores it.
- With the hook, C2 can clear this session's junk, processes and worktrees as S1.
- The ledger is evidence, not authority. The engine still re-checks each fingerprint
  before acting.
- The hook's tests must prove the fail-open paths (HS-10).
