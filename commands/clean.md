---
description: Project housekeeping at a level and scope - /clean minimal | light | standard | deep | immaculate [session|repo|machine] [audit]
argument-hint: "[minimal|light|standard|deep|immaculate|1-5] [session|repo|machine] [audit]"
---

## Context

- Repository: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repository"`
- Branch and changes: !`git status --short --branch 2>/dev/null | head -25`
- Arguments: $ARGUMENTS

## Your task

Run a housekeeping pass with the **tidy** skill from this plugin (Skill tool:
`housekeeping-skills:tidy`, or `tidy`). Follow it exactly: record → land → clear → verify →
report, gating every removal by its safety class.

Read the arguments case-insensitively. The first word that matches each column wins.

| Level word | Level |
|---|---|
| `minimal`, `1`, `save`, `checkpoint` | **Minimal**: preserve the work and record where things stand |
| `light`, `2`, `wrap`, `wrap-up` | **Light**: put away what you just used |
| `standard`, `3`, `tidy`, `done`, `finish` | **Standard** (default): the routine checklist |
| `deep`, `4` | **Deep**: the places routine housekeeping misses |
| `immaculate`, `5`, `spotless`, `white-glove` | **Immaculate**: Deep, plus a verified disposition for every in-scope item |
| *(none)* | infer the level from context, as the tidy skill describes, and say which you chose and why |

| Scope word | Scope |
|---|---|
| `session`, `mine` | only what this session created |
| `repo` *(default)* | this repository and this project's containers, processes, and Claude Code state |
| `machine`, `all`, `global` | + global caches, all Docker, the plugin cache, deleted projects' transcripts, user settings |

If the arguments include `audit`, `plan`, `dry-run`, or `status`, stop after the survey:
- run `hk status` and `hk plan --level <l> --scope <s>`;
- show the plan table and the findings;
- change nothing: no commits, no tracker writes, no removals.

State the level, the scope, and the reason in the first line, then proceed. Ask with
AskUserQuestion only where the skill says to:
- the S2 batch approval;
- per-item S3 confirmation;
- going higher or wider than the user named.
