---
# yaml-language-server: $schema=../../.lore/schemas/adr.schema.json
type: ADR
title: Defer branch, PR and promotion policy to opum-sdlc
tags:
  - architecture
  - git
summary: When opum-sdlc is installed its rules govern branch naming, merge strategy and promotion; otherwise a generic fallback applies. The plugin adds only classification and gates.
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:18.839Z
---

# Defer branch, PR and promotion policy to opum-sdlc

## Status

Accepted (2026-09-26). Decided by the user.

## Context

Landing work means choosing a branch name, a merge strategy, when to delete a branch, and
how `dev` is promoted to `main`. In the Opum fleet those rules already exist, in the
`opum-sdlc` skill of the opum-workflow plugin (0.10.8 at the time of writing):
- branches are `<type>/<TASK-ID>-<slug>` off `origin/dev`, and the task exists first;
- one task, one branch, one PR, squash-merged into `dev`;
- promotion is fast-forward only, landed with `git push origin origin/dev:main` after a PR
  runs checks on that SHA, and verified by tree equality;
- "A branch with unique commits is unlanded work, not clutter… This is the only
  irreversible mistake."

`opum-sdlc` also ships an estate audit (`sdlc-audit`) and a PreToolUse guard that blocks
commits on `dev` or `main`. It says it automates "the refusal, never the destruction".

Outside the fleet there is no such skill, and branching models differ. GitFlow, trunk-based
development and "merge release to main" each need different promotion checks. See
[State of the art, section 2](../reference/state-of-the-art-in-agentic-housekeeping.md#2-git-hygiene).

## Decision

- **When `opum-sdlc` is installed, its rules govern** branch naming, merge strategy,
  promotion, and which branches are trunk and release. `git-hygiene` follows them and does
  not restate them.
- **Otherwise a generic fallback applies.** The trunk is `origin/HEAD`. Merges are squash
  by default. Promotion happens only when the user asks, through a PR. `.housekeeping.toml`
  `[sdlc]` can override each value.
- **The plugin adds only two things in either case:** the landed/unlanded classification
  and the safety gate
  ([R-5](../specs/cleanliness-levels.md#r-5-a-branch-with-unique-commits-is-unlanded-work-not-clutter)).
- The engine never merges, pushes or promotes. Those are landing operations the skill
  performs directly. The engine only probes their state.

Rejected alternatives:
- **Re-implementing the fleet's rules in this plugin.** Two copies of the same policy
  drift, and the fleet's copy is the one its CI enforces.
- **Requiring `opum-sdlc`.** The plugin must work in any repository.
- **Hard-coding one branching model for everyone.** Each model needs different promotion
  checks, and forcing one is out of scope for housekeeping.

## Consequences

- In the fleet, housekeeping never contradicts the SDLC skill. Its gate is stricter or
  equal, never looser.
- `git-hygiene` must detect `opum-sdlc` at runtime and say in its plan which policy is in
  force.
- The spec's open question on the estate audit stands: classify natively, and cross-check
  against `sdlc-audit --json` when available, reporting any disagreement.
- Outside the fleet, users get safe defaults but may need to set `[sdlc]` for GitFlow-style
  repositories.
