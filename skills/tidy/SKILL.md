---
name: tidy
description: Project housekeeping after agentic engineering work, at a chosen level - Minimal (save a recoverable stopping point), Light (put away what you just used), Standard (the routine checklist, the default), Deep (the places routine housekeeping misses), or Immaculate (deep, plus verify every in-scope item has an intentional disposition) - within a scope of session, repo, or machine. Use this skill whenever the user wants to tidy up, clean up, wrap up, "land the plane", close out a session or a task, finish a branch, do a deep clean, free disk space, or leave the project immaculate or spotless - including casual asks like "tidy up", "clean up after yourself", "we're done, put everything away", "deep clean this repo", "leave nothing behind before the handover", or "what's left lying around?". It picks the level and scope from context, runs record -> land -> clear -> verify -> report in that order, and never removes anything irreversible without a per-item confirmation.
---

# tidy

This is **project housekeeping**: commits, branches, worktrees, caches, containers, issue
statuses, docs, and handoffs. It does **not** improve the code itself, so there is no
formatting, dead-code removal, or refactoring here.

Three settings govern every pass:

| Setting | Values | Decides |
|---|---|---|
| **Level** (`housekeeping_level`) | minimal · light · **standard** (default) · deep · immaculate | *how much* housekeeping; each level includes everything below it |
| **Scope** (`housekeeping_scope`) | session · **repo** (default) · machine | *where* it may act; a level never widens the scope |
| **Safety class** (per operation) | S0 · S1 · S2 · S3 | *how each removal is gated*, whatever the level |

| Level | Meaning |
|---|---|
| **Minimal** | Preserve the work and record where things stand. Leave a recoverable stopping point, and nothing more. |
| **Light** | Put away what you just used. Commit completed work, update the immediate issue, remove task-generated temporary files. |
| **Standard** | The routine checklist. Reconcile commits and issue statuses, update relevant docs and handoff notes, remove known disposable artifacts (landed branches, this project's stopped containers, reviewed junk). |
| **Deep** | The places routine housekeeping misses: stale branches and worktrees, disposable caches and build outputs, outdated status information, obsolete docs, leftover artifacts, Claude Code debris. Resolve what is safe and authorized. |
| **Immaculate** | Deep, **plus verify the final state**. Every in-scope change, branch, issue, document, and artifact has an intentional disposition. Nothing is forgotten, ambiguous, or unaccounted for. |

The top level is "verify that no applicable chores remain", not "delete everything". A kept
`.env`, a `retain/` branch, or a task deferred to a follow-up is immaculate once its
disposition is stated. **Nothing left unattended, not nothing left on disk.**

| Class | Meaning | Gate |
|---|---|---|
| S0 | read-only | none |
| S1 | reversible, with the undo journalled (trash, archive ref, stop) | runs within the level and scope; listed in the plan |
| S2 | regenerable at a cost (build outputs, caches, images, stopped containers) | **one batch approval** |
| S3 | irreversible (unlanded commits, volumes, unknown untracked files, transcripts) | **confirmed per item, by name** |

`references/levels.md` has the full table of what each level adds per phase, per scope. Read
it when a case isn't covered here.

## The engine

Removal goes through `hk`, a stdlib Python engine shipped with this plugin. It
inventories, classifies, plans, and applies **exactly** the plan. It re-checks every
target, journals every action with its undo, and refuses anything protected or out of
scope. Its state lives in `.git/housekeeping/`, never in the working tree.

The Skill tool printed `Base directory for this skill: <dir>`. The engine is
`<dir>/../../scripts/hk.py`:

```bash
HK="python3 <dir>/../../scripts/hk.py"
$HK doctor            # which tools (gh, docker, quest, lore, trash) are available here
```

Never remove things with ad-hoc shell instead of `hk`: no `rm -rf "$VAR"`, no
`git clean -fdx`, no loops over `git branch | grep`. The worst agent cleanup incidents on
record deleted a home directory through an unresolved variable in a generated script. If
`hk` refuses an item, report the refusal. Do not route around it.

## Workflow

### 1. Choose the level and scope, and say which and why

If the user named a level (`/clean deep`, "a light tidy", "make it immaculate"), use it.
Otherwise infer it:

1. Context is about to run out, an emergency stop, "save where we are" → **Minimal**.
2. The session is ending, "wrap up for today", a handoff → **Light**.
3. A bare "tidy up" or "clean up"; a task just finished, a PR merged, "close this out" →
   **Standard**.
4. "Deep clean", "things have piled up", low disk space → **Deep**.
5. "Immaculate", "spotless", "leave nothing behind"; before a release, a handover, or an
   audit → **Immaculate**.

Scope is `repo` unless the user says otherwise:
- **session**: "just what you did", "your own mess".
- **machine**: the whole machine, overall disk space, global caches, all of Docker,
  `~/.claude`, other projects' leftovers.

"Deep clean" alone is Deep **at repo scope**. It does not license a machine-wide purge. If
the request mentions machine-wide things, confirm machine scope with one AskUserQuestion
(recommend repo unless they clearly meant the machine).

`.housekeeping.toml` may set `housekeeping_level`, `housekeeping_scope`, and `[levels]`
context defaults. Start with one line: "Standard housekeeping, repo scope: PR #42 for HS-4
just merged." When unsure, choose the lower level or the narrower scope, and mention the
other. Never go higher or wider than the user asked without asking.

### 2. Survey (read-only)

```bash
$HK status --json                                                   # branch, trunk, ahead/behind, tracker, lore, PRs
$HK plan --level standard --scope repo --chosen-by "PR merged" --json
```

Read the plan's:
- `items`: what would be removed;
- `findings`: what needs a human decision, including everything protected;
- `notes`: what the engine could not check, such as a missing `gh` or Docker daemon.

A note is a fact to report. "No PR-state proof available" is not the same as "no landed
branches".

### 3. Record: durable before disposable

Record before clearing. Clearing can destroy what the record needs: a log, a scratch result,
the worktree holding an uncommitted fix. Use the **session-sync** skill:

| Level | Record |
|---|---|
| Minimal | a progress note: where things stand, and what is next |
| Light | + update the immediate issue; criteria checked with evidence |
| Standard | + reconcile statuses with commits; update relevant docs and handoff notes; close a finished task in its delivering PR; run the tracker and docs gates |
| Deep | + outdated status information, obsolete docs, two-way spec drift |
| Immaculate | + a disposition for every task and document the session touched |

### 4. Land

Use the **git-hygiene** skill:

| Level | Land |
|---|---|
| Minimal | preserve the work: commit (a WIP commit if needed) on the task branch, and push |
| Light | commit completed work in logical units, and push |
| Standard | + open or refresh the PR; merge when the checks are green; delete the local branch after its merge (no automation does that step) |

When `opum-sdlc` is installed, its rules govern branch names, merge strategy, and
promotion. Promote to a release branch only when the user asked for it.

### 5. Re-plan, then clear

Landing changes what is removable: a branch you just merged is now provably landed. So plan
again after landing:

```bash
$HK plan --level <level> --scope <scope> --chosen-by "..."     # prints the table and "Plan saved: <path>"
```

Show the user the plan table. Then gate each item by its class:
- **S1** runs without asking. It is reversible, and the table showed it.
- **S2** needs **one** batch approval. Use AskUserQuestion, giving the count and total size.
  Recommend approval when the batch is what the level promises: "Remove 14 regenerable
  items (2.3 GB: node_modules, dist, .pytest_cache)? Recommended: yes." If the user
  approved only part of the batch (for example "regenerable stuff" but not junk-named
  files), apply that part with `--only <ids>`.
- **S3** needs **each item** confirmed by name. Use AskUserQuestion with
  `multiSelect: true`, listing each item: its id, its target, and why it is irreversible.
  Preselect nothing, and don't offer an "all" option.

```bash
$HK apply <plan.json> --approve-s2 --confirm id1,id2      # omit the flags the user did not grant
```

Hand the domain judgement calls to the domain skills:
- **workspace-clean**: is this `*_v2.py` junk, or real work?
- **runtime-clean**: whose dev server is this?
- **harness-hygiene**: Deep proposals for memory, CLAUDE.md, permissions, and plugins.

These propose; the user approves. `apply` exits `0` when every attempted item succeeded,
`5` when an item changed since planning (it was skipped), and `6` when an item failed.
Report skipped and failed items; don't retry around them.

### 6. Verify

| Level | Verify |
|---|---|
| Minimal | The work is recoverable: committed and pushed, or its location is recorded on the task. |
| Light | + no process this session started is still running; none of its temp files is left |
| Standard | + `$HK plan --level standard` plans no landed branch; the tracker and docs gates pass; `git status` is clean or every remaining change is explained |
| Deep | + bytes reclaimed, from the apply summary |
| Immaculate | + **every in-scope item has a disposition**, and the final-state checks pass (below) |

**Immaculate verification.**

```bash
$HK disposition --level immaculate --scope <scope>          # lists every in-scope item; UNACCOUNTED ones fail it
$HK disposition --level immaculate --scope <scope> \
    --set <id>=kept:"retain/ branch, reason in docs/…" \
    --set <id>=deferred:"HS-14" --set <id>=accepted:"local IDE config"
```

Dispositions:
- **kept**, with the reason;
- **removed**;
- **landed**;
- **deferred**, to a named task;
- **accepted**, a known, deliberate state.

Protected and keep-list items are disposed as kept automatically. Record each disposition
from evidence or from the user's answer, never a guess. The pass is immaculate only when
`hk disposition` exits 0 **and** the `[immaculate] verify` commands exit 0. Those commands
default to the repo's own install, build, and test (read them from `.housekeeping.toml`,
the README, or CI). Record each command with its exit code.

### 7. Report

End with the report from `references/report.md`:
- the level, the scope, and why;
- what was recorded, landed, and cleared, per class;
- bytes reclaimed;
- the journal path (`hk undo <journal>` reverses the S1 items);
- what was skipped, and why;
- findings outside the scope.

An Immaculate pass also includes the **disposition record**.

## Never, at any level or scope

- **Mutate another repository's working tree.** Each repo has one live session that owns
  its mutations. Report its state instead; don't change it.
- **Touch the protected set:**
  - trunk and release branches, and the checked-out branch;
  - `retain/`, `preserve/`, and `archive/` branches;
  - tracked files, `.env*`, keys, `.quest/`, `docs/`, and `.lore/`;
  - the self-hosted CI runner `opum-runner` and its image;
  - the current session's own transcript and scratchpad.
- **Remove what the user said to keep.** Add it to `[protect]` in `.housekeeping.toml` so
  the next pass honours it too, and say so.

## When things are missing

- **No quest or lore:** record in whatever tracker the repo uses, or say none was found.
- **No remote:** containment is proven against local branches only. Say so.
- **No Docker daemon, no `gh`, or no trash tool:** `hk` notes it and adjusts. Without a
  trash tool, removals are permanent, so trash items are raised a class. Pass the note on.
