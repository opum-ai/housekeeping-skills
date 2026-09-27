# quest and lore: exact commands and traps

Verified against quest 0.10.0 and lore 0.9.3 (2026-09-26). The installed CLI's
`quest instructions <guide>`, `quest help <cmd>`, and `lore instructions <topic>` win when
they disagree with this page.

## Contents
- Envelopes and exit codes
- Quest: find, record, close
- Lore: find, write, gate
- How they interact
- Traps

## Envelopes and exit codes

Both CLIs:
- accept `--json` and write `{schemaVersion, kind, data, ...}` to stdout;
- write errors to stderr.

| Exit | Meaning | What to do |
|---|---|---|
| 0 | ok | read the payload: `quest doctor`, `lore orphans`, and `edit-batch` exit 0 with findings |
| 2 | usage | fix the flags (`quest help <cmd>`) |
| 3 | not found | wrong id, or a Story naming a missing task (fix with `lore unlink`) |
| 4 | denied | missing or wrong actor flags |
| 5 | conflict | re-read the task, reapply, and retry a bounded number of times; quest never retries for you |
| 6 | validation / drift | an illegal transition, an out-of-range AC, agents drift, or `lore check` failures |
| 7 | indeterminate (lore) | lore cannot judge from here; never "fix" it with `lore schema export` |

Never pipe a quest write through `grep` or `tail`: the pipe hides its exit code.

## Quest

```bash
A=(--actor "$ACTOR" --actor-kind delegated-agent --accountable-human "$HUMAN" --json)

quest task list --status "In Progress" --json      # read .scope {branch, otherRefsRead, unseenTaskIds}
quest task list --ready --json                     # dependencies satisfied
quest task list --unresolved-at-completion --json  # closed with unchecked criteria
quest task view HS-4 --json                        # acceptanceCriteria[].position is 1-based
quest search "words" --json                        # before creating anything

quest task start HS-4 "${A[@]}"
quest task edit HS-4 --add-note "Established … / Blocked … / Next …" "${A[@]}"
quest task edit HS-4 --add-reference https://github.com/o/r/pull/42 --add-modified-file skills/tidy/SKILL.md "${A[@]}"
quest task edit HS-4 --check-ac 1 --check-ac 3 "${A[@]}"            # only with evidence
quest task edit HS-4 --append-final-summary "Review changed …" "${A[@]}"
quest task complete HS-4 --final-summary "What, why, how verified: PR #42, CI run 123456" "${A[@]}"
quest task pause HS-4 "${A[@]}"                                     # the only way to Paused

quest task create "Title" --parent HS-1 --description "why" \
  --acceptance-criteria '["observable outcome"]' "${A[@]}"
quest draft create "Idea not yet committed work" "${A[@]}"

quest doctor --json                                  # data.healthy, data.issues[]
quest agents --check --require-installed --target claude   # target defaults to codex: pass claude
```

- No `task delete` exists. Close a task with `complete`, `archive`, or `demote --to`.
- `quest cleanup` is a dry run unless you pass `--confirm`. It removes closed,
  unreferenced milestones and superseded decisions, never tasks. Use it only with the
  user.
- quest never commits `.quest/`. You commit it, with the code, on the task branch.

## Lore

```bash
lore query "cleanliness levels" --limit 5 && lore read specs/cleanliness-levels
lore new story "Title" --summary "…" --tags a,b     # also: adr, spec, reference, runbook, epic
lore link stories/tidy-orchestrator-skill HS-4      # needs LORE_QUEST_ACTOR, _ACTOR_KIND, _ACCOUNTABLE_HUMAN
lore tasks stories/tidy-orchestrator-skill          # the live rollup of linked tasks
lore sync                                           # regenerate managed blocks and status rollups
lore check                                          # the gate: drift, links, anchors, schema (exit 6 on findings)
lore orphans --json                                 # tasks without docs, links to missing tasks (exits 0)
lore agents --check                                 # bridge drift (6 = a hand-edited or stale bridge)
```

- A Story has two status fields:
  - `lore_task_status` is the rollup that `sync` writes;
  - `status` (draft/stable/deprecated) is hand-authored.
- `docs/log.md` is generated from commits that touch `docs/`. Hand-written lines are
  dropped. Session history reaches it through good commit subjects.

## How they interact

With `[tracker] backend = "quest"`, a quest status move makes the linked Stories drift.
- **Sequence:** quest write → `lore sync` → `lore check` → commit `.quest/`, `docs/`, and
  the code together.
- **Automation:** opum-workflow's PostToolUse hook runs the sync for you and names the
  files it rewrote. Commit them in the same change.

## Traps

1. **`task edit --status Done` does not complete a task.** A later `complete` fails with
   "Done -> Done" (exit 6). Recover with `demote --to "In Progress"`, then `complete`.
2. **Unchecked criteria don't block `complete`.** They are saved as
   `unresolvedAtCompletion`. Check or explain each one before closing.
3. **`--check-ac` takes the 1-based `position`, not the 0-based `index`.** Positions
   renumber after `--remove-ac`, so re-read the task.
4. **`--final-summary` replaces the summary.** Use `--append-final-summary` to extend it.
5. **`lore link` without the actor env still writes the Story side.** Set the three
   `LORE_QUEST_*` variables first.
6. **`lore link` strips the Story's `# yaml-language-server: $schema=…` line, even on
   success** (lore 0.9.3). After linking, check line 2 of the Story and restore it.
   `lore check` does not flag its absence.
7. **The In Progress listing is branch-scoped.** Read `scope`, and cross-check
   `gh pr list --state open`.
