---
description: Housekeeping at a cleanliness level - /clean tidy | sweep | done | deep | room (or c1-c5); add "audit" for a read-only plan
argument-hint: "[tidy|sweep|done|deep|room|c1-c5] [audit]"
---

## Context

- Repository: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repository"`
- Branch and changes: !`git status --short --branch 2>/dev/null | head -25`
- Arguments: $ARGUMENTS

## Your task

Run a housekeeping pass with the **tidy** skill from this plugin (Skill tool:
`housekeeping-skills:tidy`, or `tidy`). Follow it exactly: record → land → clear → verify →
report, gating every removal by its safety class.

Map the arguments to a level. Matching is case-insensitive, and the first word that
matches wins:

| Argument | Level |
|---|---|
| `tidy`, `c1`, `wrap`, `wrap-up` | **C1 Tidy**: tracker note, logical commits, push; nothing removed |
| `sweep`, `c2` | **C2 Sweep**: + this session's junk, processes, clean worktrees; the docs it touched |
| `done`, `clean`, `finish`, `c3` | **C3 Clean**: + close the task, merge, prune landed branches and worktrees, project containers |
| `deep`, `deep-clean`, `c4` | **C4 Deep clean**: + build outputs, deps, caches, stale branches (archived), temp leaks, harness debris |
| `room`, `cleanroom`, `clean-room`, `scrub`, `pristine`, `c5` | **C5 Clean room**: + fresh-clone checkout, global caches, machine Docker, rebuild-from-scratch proof |
| *(no level word)* | infer it from context, as the tidy skill describes, and say which level you chose and why |

If the arguments include **`audit`**, `plan`, `dry-run`, or `status`, stop after the survey:
- run `hk status` and `hk plan` at the level;
- show the plan table and the findings;
- change nothing: no commits, no tracker writes, no removals.

State the level and the reason in the first line, then proceed. Ask with AskUserQuestion
only where the skill says to:
- the S2 batch approval;
- per-item S3 confirmation;
- going above the level the user named.
