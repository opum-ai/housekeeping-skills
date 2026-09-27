---
name: session-sync
description: Reconcile the tracker and the docs with what this session actually did - progress notes, acceptance criteria checked only with evidence, tasks closed the right way, follow-up tasks for discovered work, lore docs updated and gated, and two-way spec drift resolved. Native to quest (tasks) and lore (docs); falls back to GitHub issues or plain notes. Use this skill whenever the user asks to update the issue, quest, task, ticket, tracker, or docs from this session - "record progress", "close out HS-12", "mark the task done", "update the story", "sync the docs", "the spec is out of date", "leave notes for the next session", "write up what we did" - and at the Record phase of every housekeeping pass, even when the user only said "wrap up".
---

# session-sync

The tracker and the docs are the durable record. The session is not: whatever it
established and did not write down dies with it. This skill turns a session's work into
records that someone else can verify. It runs **before** anything is cleared, because
clearing can destroy the evidence a record needs.

Exact command syntax and known traps are in `references/quest-lore.md`. Read it before
your first quest or lore write in a session.

## 0. Detect what the repo uses

| Signal | Tracker / docs |
|---|---|
| `.quest/` and `quest` on PATH | quest tasks |
| `.lore/` and `lore` on PATH | lore docs (`[tracker] backend = "quest"` couples Stories to tasks) |
| neither, a GitHub remote, and `gh` | GitHub issues (comment only when the user asks) |
| nothing | say so; offer notes in the PR body or a handoff |

Run `quest instructions task-execution` and `quest instructions task-finalization` when
the repo uses quest. The installed CLI's own guide wins over anything written here.

**Actor.** Every quest write declares an actor:
`--actor <id> --actor-kind delegated-agent --accountable-human <id>`. Look for the ids in:
1. `OPUM_HOOK_ACTOR` / `OPUM_HOOK_ACCOUNTABLE_HUMAN`;
2. `.claude/settings.json` `env`;
3. the repo's existing task records (`quest task view <id> --json`, author fields).

Ask the user once if none is found. An agent session is never `--actor-kind human`.

## 1. Gather what happened

The state is live and verifiable. Your memory of the session is neither.
- `git log --oneline <trunk>..HEAD` and `git diff --stat <trunk>...HEAD` show what
  changed.
- `quest task list --status "In Progress" --json` shows what is claimed. Read its `scope`
  key: the listing only sees this branch.
- `quest task view <id> --json` gives the acceptance criteria (1-based `position`), notes,
  and references.
- `gh pr list --head <branch> --json number,url,state` shows the PR, if any.
- The evidence: test runs, CI run ids (`gh run list --branch <b> --limit 3`), commands you
  ran and their exit codes.

## 2. Record, by level

### Minimal and Light (every pass)
Minimal stops after the progress note: its only job is a recoverable stopping point. Light
also updates the immediate issue: its criteria, references, and modified files.
- **Progress note** on each task the session touched: what was established, what is
  blocked, and what is next. Reference things by id (commit, PR, doc) instead of pasting
  them.
  ```bash
  quest task edit HS-4 --add-note "Established: … Blocked: … Next: …" <ACTOR> --json
  ```
- **Criteria**: check an acceptance criterion **only with evidence in hand**. A criterion
  checked on faith is worse than one left open, because it stops anyone else from looking.
  For each one you check, name the evidence in the note ("AC2: `pytest` 20 passed, CI run
  123"). A criterion you cannot prove stays unchecked, with the reason noted.
- `--add-reference <PR url>` and `--add-modified-file <path>` when they help the next
  reader.

### Standard (the default): the routine checklist
- **Docs the session touched.**
  1. Find the related concepts with `lore query "<topic>" --limit 5`, then `lore read <id>`.
  2. Update the prose **outside** the managed blocks (`<!-- lore:… -->`). `lore sync`
     overwrites anything inside them.
  3. A new decision that governs later work gets an ADR (`lore new adr "…"`). Routine work
     doesn't.
- **Follow-up work.**
  1. Work discovered outside the task's criteria becomes a *new* task, not a silent
     addition. Search first (`quest search "<words>" --json`); create only if nothing
     matches.
  2. Write the criteria as outcomes someone else can verify.
  3. Link a dependency only when the new task truly blocks on it.

### Standard, when the task is finished
- **Close the task in the PR that delivers its last criterion.**
  1. Check the criteria that the evidence proves.
  2. Run `quest task complete <id> --final-summary "<what, why, how verified: PR #N, CI run <id>>"`.
  3. Cite the **PR number and CI run id**, both knowable before the merge. **Never cite
     the merge SHA**: that forces a second closing PR.

  Close only with `quest task complete`. `task edit --status Done` leaves the record in
  place, and a later `complete` then fails with "Done -> Done".
- **Gates**, all of which read their payload (several exit 0 on findings):
  ```bash
  lore sync && lore check                                  # exit 0 required; commit the sync output
  quest agents --check --require-installed --target claude # 6 = managed instructions drifted
  lore agents --check
  quest doctor --json                                      # read data.healthy; the exit code is 0 either way
  lore orphans --json                                      # offer lore link / unlink for what it finds
  ```
- **Commit together**: the `.quest/` change, the `lore sync` output, and the code go in
  **one commit** (the git-hygiene skill stages them). A tracker status move is a docs
  change in a lore-coupled repo: the Story's task block goes stale the moment the task
  moves.

### Deep: outdated status, obsolete docs, two-way spec drift
For each spec, Story, or ADR requirement the session's changes touch, compare it with the
code. Resolve each mismatch in **one** of three ways, and say which:
1. **Fix the code.** The spec is right. File or continue a task.
2. **Amend the spec.** The code is right and the spec is stale. Edit the spec, and note
   the reason in the same commit.
3. **Record a deviation.** Both stand for now. Add an ADR, or a "Deviations" note in the
   spec that names the task that will close the gap.

Never silently rewrite a spec to match the code. That erases the decision that someone
made. Tools that reconcile only one way (code catches up to spec, or spec catches up to
code) are how drift hides.

### Immaculate: a disposition for everything touched
Every task and document the session touched gets an intentional disposition:
- **landed**: completed, citing the PR and CI run;
- **deferred**: to a named follow-up task;
- **kept**: with the reason;
- **accepted**: a known, deliberate state.

Put the summary of the tidy report's disposition record on the task (as a note or with
`--append-final-summary`), and the full record in the PR body.

## 3. Before reporting "nothing open"

The listing is branch-scoped. A task In Progress on an unmerged branch is invisible from
`dev`.
- Read `scope`: `otherRefsRead: false` is not a clear, and `unseenTaskIds` names ids to go
  and look at.
- **Cross-check** `gh pr list --state open`.
- Fetch with `--prune` first, or both detectors inherit stale refs.

## 4. Handoff

If the session stops on a decision only a person can make, or before a forced renewal:
- ask with AskUserQuestion when the person is present;
- otherwise hand off with the `opum-handoff` skill if it is installed, or leave a note on
  the task with the question, the options, and your recommendation.

A finished task, an opened PR, or a merged branch is not a handoff; it is a report.

## Without quest or lore

- **GitHub issues**: `gh issue comment <n> --body …`, only when the user asked. Closing an
  issue is the user's call unless the PR says `Fixes #n`.
- **Plain repos**: put the record in the PR description, or in a
  `docs/`/`CHANGELOG.md` entry if the repo keeps one. Never invent a new tracker file.
