---
name: tidy
description: Clean up after agentic engineering work at a chosen cleanliness level, from C1 Tidy (tracker notes, logical commits, push) through C3 Clean (merge, prune landed branches and worktrees) to C5 Clean room (fresh-clone checkout, purged caches and Docker, rebuild-from-scratch proof). Use this skill whenever the user wants to wrap up, tidy up, clean up, "land the plane", close out a session or a task, finish a branch, free disk space, deep clean, or make a repo or machine pristine - including casual asks like "clean up after yourself", "we're done, tidy everything", "leave it clean", "scrub everything before the release", or "what's left lying around?". It picks the level from context, runs record -> land -> clear -> verify -> report in that order, and never removes anything irreversible without a per-item confirmation.
---

# tidy

Housekeeping has two dials, and this skill turns both:

- **The cleanliness level (C1-C5)** decides *how far* a pass reaches. Each level includes
  everything below it.
- **The safety class (S0-S3)** of each operation decides *how it is gated*, whatever the
  level. Choosing C5 widens the scope; it never makes an irreversible deletion any less
  irreversible.

| Level | Name | Adds |
|---|---|---|
| C1 | Tidy | Tracker progress note, logical commits on the task branch, push. Nothing is removed. |
| C2 | Sweep | This session's junk files, processes and dev servers, and clean worktrees; the docs it touched; stash review. |
| C3 | Clean | Close the task, merge per the SDLC, prune landed branches (local and remote), prunable worktrees, stale refs, this project's stopped containers, orphaned processes in the repo; tracker/docs gates. |
| C4 | Deep clean | Build outputs, dependency dirs, project caches and images, old stashes, stale unlanded branches (archived first), `$TMPDIR` leaks, old session scratchpads, Claude Code harness debris and bloat proposals. |
| C5 | Clean room | Checkout reset to fresh-clone state (minus a keep-list), global caches, machine-wide Docker, then **prove** it rebuilds from scratch and certify what remains. |

| Class | Meaning | Gate |
|---|---|---|
| S0 | read-only | none |
| S1 | reversible, undo recorded (trash, archive ref, stop) | runs within the level, listed in the plan |
| S2 | regenerable at a cost (build outputs, caches, images) | **one batch approval** |
| S3 | irreversible (unlanded commits, volumes, untracked unknown files, transcripts) | **confirmed per item, by name** |

The full design is `references/levels.md`. Read it when a case is not covered here.

## The engine

Removal goes through `hk`, a stdlib Python engine shipped with this plugin. It inventories
candidates, classifies each one, writes a plan, and applies **exactly** the plan. It
re-checks every target, journals every action with its undo recipe, and refuses anything
protected or outside its reach.

The Skill tool printed `Base directory for this skill: <dir>` when this skill loaded. The
engine is `<dir>/../../scripts/hk.py`. Set it once:

```bash
HK="python3 <dir>/../../scripts/hk.py"
$HK doctor            # which tools (gh, docker, quest, lore, trash) are available here
```

Never remove things with ad-hoc shell instead of `hk`. That rules out `rm -rf "$VAR"`,
`git clean -fdx`, and loops over `git branch | grep`. The two worst agent cleanup incidents
on record both deleted a home directory through an unresolved variable in a generated
script. `hk` exists so every deletion is a resolved, fingerprinted, containment-checked
path that a person saw in a plan. If `hk` refuses an item, the refusal is the answer:
report it; do not route around it.

## Workflow

### 1. Choose the level, and say which and why

If the user named a level (or a synonym such as "deep clean" or "clean room"), use it.
Otherwise infer it:

1. The session is ending, compacting, or handing off → **C1**.
2. A bare "clean up", "tidy", or "sweep" → **C2**.
3. The task is finished, a PR merged, or "close out this branch" → **C3**.
4. Low disk space, "deep clean", or a slow machine → **C4**.
5. "Pristine", "clean room", or "scrub"; before a release, benchmark, demo, or handover → **C5**.

`.housekeeping.toml` `[levels]` may set these defaults for the repo. State the level and
the reason in one line before doing anything ("Running C3 Clean: the PR for HS-4 just
merged."). When unsure between two levels, choose the lower one and mention the higher
one. Never go *above* what the user asked without asking.

### 2. Survey (read-only)

```bash
$HK status --json                                        # branch, trunk, ahead/behind, tracker, lore, PRs
$HK plan --level C3 --chosen-by "PR merged" --json       # everything removable at this level, classified
```

Read the plan's `items` (what would be removed), `findings` (what needs a human decision,
including everything protected), and `notes` (what the engine could not check, such as a
missing `gh` or Docker daemon). A note is a fact to report. "No PR-state proof available"
is different from "no landed branches".

### 3. Record: durable before disposable

Record before clearing, because clearing can destroy what the record needs: a log, a
scratch result, the worktree holding an uncommitted fix. Use the **session-sync** skill to
reconcile the tracker and docs with what the session did:
- C1: a progress note, and acceptance criteria checked with evidence;
- C2: the lore docs the session touched, and follow-up tasks;
- C3: close the task in its delivering PR, then run the gates;
- C4: two-way spec drift.

### 4. Land

Use the **git-hygiene** skill:
- C1: logical commits on the task branch, then push.
- C2: open or refresh the PR.
- C3: merge when the checks are green, and delete the local branch after the merge (no
  automation does that step).

When `opum-sdlc` is installed, its rules govern branch names, merge strategy, and
promotion. Promotion to a release branch happens only when the user asked for it.

### 5. Re-plan, then clear

Landing changes what is removable: the branch you just merged is now provably landed.
Plan again after landing, so the plan reflects the current state:

```bash
$HK plan --level C3 --chosen-by "..."     # prints the plan table and "Plan saved: <path>"
```

Show the user the plan table. Then gate by class:
- **S1** items run without asking. They are reversible, and the table already showed them.
- **S2** items need **one** batch approval. Use AskUserQuestion with the count and total
  size, recommending approval when the items are what the level promises: "Remove 14
  regenerable items (2.3 GB: node_modules, dist, .pytest_cache)? Recommended: yes." If
  the user declines, drop the S2 flag.
- **S3** items need **each one** confirmed by name. Use AskUserQuestion with
  `multiSelect: true`, listing each S3 item (id, target, and why it is irreversible).
  Nothing is preselected, and no "all" option is offered. Only the ids the user selects
  are confirmed.

```bash
$HK apply <plan.json> --approve-s2 --confirm id1,id2      # omit the flags the user did not grant
```

For judgement calls inside a domain, use the domain skills:
- **workspace-clean**: is this `*_v2.py` junk or real work?
- **runtime-clean**: whose dev server is this?
- **harness-hygiene**: C4+ memory, CLAUDE.md, permission, and plugin proposals.

These skills never edit settings or memories on their own. They propose, and the user
approves.

`apply` exits:
- `0`: everything it attempted succeeded;
- `5`: an item changed since planning and was skipped;
- `6`: an item failed.

Report skipped and failed items rather than retrying around them.

### 6. Verify

| Level | Verify |
|---|---|
| C1 | `git status` is clean, or every remaining change is explained; the branch is pushed (`ahead 0`). |
| C2 | No ledger-recorded process is still running; no ledger junk is left. |
| C3 | `$HK plan --level C3` plans no landed branch; the tracker and docs gates pass. |
| C4 | Bytes reclaimed, from the apply summary. |
| C5 | **Rebuild from scratch**: run the repo's install, build, and test (`[cleanroom] verify` in `.housekeeping.toml`, or the commands in the README/CI). Record each command and its exit code. A clean room that cannot rebuild is not clean; it is broken. |

### 7. Report

End with the report from `references/report.md`:
- the level and why it was chosen;
- what was recorded, landed, and cleared, per class;
- bytes reclaimed;
- the journal path (`hk undo <journal>` reverses the S1 items);
- what was skipped and why;
- findings outside this pass's reach (other repos, protected items, unlanded branches).

A C5 pass also writes the clean-room certificate into the report.

## Reach: what this skill never touches

- **Other repositories' working trees, at any level.** Each repo has one live session
  that owns its mutations. Report their state; do not change it.
- **The protected set:**
  - trunk and release branches, and the checked-out branch;
  - branches under `retain/`, `preserve/`, and `archive/`;
  - tracked files, `.env*`, keys, `.quest/`, `docs/`, and `.lore/`;
  - the self-hosted CI runner container `opum-runner` and its image;
  - the current session's own transcript and scratchpad.
- **Anything the user said to keep.** Add it to `[protect]` in `.housekeeping.toml` so the
  next pass honours it too, and tell the user you did.

## When things are missing

- **No quest or lore.** Record in whatever tracker the repo uses, or say none was found.
- **No remote.** Containment is proven against local branches only; say so.
- **No Docker daemon, no `gh`, no trash tool.** `hk` notes it and adjusts (with no trash
  tool, removals are permanent, so trash items are raised a class). Pass the note on.
