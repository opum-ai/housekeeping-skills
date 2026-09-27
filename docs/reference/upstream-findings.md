---
# yaml-language-server: $schema=../../.lore/schemas/reference.schema.json
type: Reference
title: Upstream findings
tags:
  - research
  - upstream
summary: Dated defects, missing capabilities and usage traps observed in other repos' tools while building this plugin, written up for their owners with repros and classifications.
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:10.140Z
---

# Upstream findings

These are findings about tools this plugin depends on or cleans up after. They are
written for the tools' owners. **None has been filed.** Each owner decides whether and
where to file it.

Every finding is a dated observation from 2026-09-26. It may already be fixed in a later
version. Home paths are shown as `~`. Findings (a) to (c) were reproduced in a throwaway
sandbox (a fresh `git init` plus `quest init` and `lore init --tracker quest`). Findings
(d) to (g) come from the read-only machine inventory in
[State of the art](state-of-the-art-in-agentic-housekeeping.md#10-measured-machine-inventory-snapshot-2026-09-26).
Finding (h) comes from reading the command's source; it was not executed.

Classifications:
- **Defect.** The tool contradicts its own documentation or loses data.
- **Missing capability.** The tool behaves as documented, but a reasonable workflow needs
  something it does not offer.
- **Usage mistake.** The tool behaves as documented. The trap is in how callers use it, so
  the fix is documentation or a better error message.

## Details

### Summary

| # | Owner | Tool | Finding | Class |
|---|---|---|---|---|
| a | lore-cli | lore 0.9.3 | `lore link` writes the Story before a Quest write that fails, and strips the schema modeline even on success | Defect |
| b | quest-cli | quest 0.10.0 | `task edit --status Done` followed by `task complete` fails with "Done -> Done" | Usage mistake |
| c | quest-cli | quest 0.10.0 | `quest doctor` exits 0 when `healthy` is false | Missing capability |
| d | lore-cli, opum-cli-e2e | test suites | Test runs leak temp dirs in `$TMPDIR`: about 13,700 entries under four prefixes, in a 24 GB `$TMPDIR` | Defect |
| e | quest-cli | `quest browser` | `quest browser --port 0` processes outlive their parents for up to ten days | Missing capability |
| f | quest-cli | opum-quest plugin 0.10.0 | Each plugin version installs about 620 MB | Defect |
| g | opum-fleet | opum-workflow plugin | `.claude/handovers/` files accumulate without pruning | Missing capability |
| h | anthropics/claude-code | commit-commands `/clean_gone` | Deletes unmerged branches and dirty worktrees on `[gone]` alone | Defect |
| i | anthropics (skill-creator) | skill-creator `scripts/run_eval.py` | Parallel workers share one `.claude/commands/`, so each run sees N copies of the skill and a trigger counts only when Claude picks its own copy (~1/N) | Defect |

### (a) `lore link` half-writes on failure and strips the schema modeline

| Field | Value |
|---|---|
| Owner | lore-cli |
| Version | lore 0.9.3, `[tracker] backend = "quest"`, quest 0.10.0 |
| Workflow step | Coupling a Story to a task (`lore link`), during task creation and docs authoring |
| Classification | Defect |

**Part 1: failure path.** Minimal repro:
```
lore new story "Widget"
env -u LORE_QUEST_ACTOR -u LORE_QUEST_ACTOR_KIND -u LORE_QUEST_ACCOUNTABLE_HUMAN \
  lore link stories/widget SB-1
```
Exit code: **6**. Actual output:
```
error: Quest write requires an explicit actor declaration
hint: set LORE_QUEST_ACTOR and LORE_QUEST_ACTOR_KIND before this command, …
```
The Story file afterwards:
- has `tasks: [sb-1]` written;
- has lost line 2, `# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json`.

The task has no `doc:` label and no `documentation[]` entry. Re-running with the env set
prints `SB-1: tasks: already-linked, back-ref: added` and exits 0, which heals the link.
The modeline stays missing.

What the docs say (`lore instructions linking`): link validates every id "first and
fail[s] the whole command loud … before writing anything", and without the actor env
"the command fails closed with a `validation` error (exit 6)". The exit code matches.
The "before writing anything" promise does not.

**Part 2: success path.** A successful `lore link` also strips the modeline. Minimal repro:
```
lore new story "Widget"        # line 2 is the yaml-language-server modeline
LORE_QUEST_ACTOR=a LORE_QUEST_ACTOR_KIND=delegated-agent LORE_QUEST_ACCOUNTABLE_HUMAN=h \
  lore link stories/widget SB-1  # exit 0
sed -n 2p docs/stories/widget.md # prints "type: Arc"
```
`lore sync` does not strip it: an unlinked Story keeps its modeline through a sync. All 11
Stories in this bundle lost the line on linking and had it restored by hand. The Stories in
the test-skills bundle show the same loss. No doc says `link` rewrites frontmatter
comments. `lore check` does not flag the loss, so editors silently lose schema validation.

Suggested fix: write both sides only after the Quest write succeeds, or roll back the Story
on failure; preserve leading frontmatter comments when rewriting `tasks:`.

### (b) `task edit --status Done`, then `task complete`, fails with "Done -> Done"

| Field | Value |
|---|---|
| Owner | quest-cli |
| Version | quest 0.10.0 |
| Workflow step | Closing a task at the end of delivery |
| Classification | Usage mistake |

Minimal repro, with `A=(--actor a --actor-kind delegated-agent --accountable-human h)`:
```
quest task start SB-2 "${A[@]}"
quest task edit SB-2 --status Done "${A[@]}"   # exit 0; file stays in .quest/tasks/
quest task complete SB-2 "${A[@]}"             # exit 6
```
Actual output (stderr):
```
{"error_type":"validation","message":"Illegal task transition: Done -> Done.","principal":null}
```
What the docs say (`quest instructions task-finalization`, QCLI-221): "only `task
complete`/`archive`/`demote` relocate a record. `task edit --status <terminal>` sets the
status field in place and does not move it". So the behaviour is documented, and the
recovery is `quest task demote SB-2 --to "In Progress"`, then `quest task complete`.

The trap is that `edit --status Done` looks like a normal close and exits 0, and the
later error names neither the cause nor the recovery. Suggested fix: have the error hint
at `demote`, or have `edit --status <terminal>` warn that it does not relocate the record.
This plugin's spec already requires closing with `task complete` only
([Housekeeping levels, R-7](../specs/cleanliness-levels.md#r-7-record-and-land-follow-the-tracker-and-docs-contracts)).

### (c) `quest doctor` exits 0 when unhealthy

| Field | Value |
|---|---|
| Owner | quest-cli |
| Version | quest 0.10.0 |
| Workflow step | Tracker gate at Standard and in CI |
| Classification | Missing capability |

Minimal repro: in a sandbox, set one task's `status` to the retired literal `"Blocked"`,
then run `quest doctor --json`. Exit code: **0**. Actual output (trimmed):
```
{"kind":"project.doctor","data":{"healthy":false,"issues":[{"code":"task_status_off_flow",
 "taskId":"SB-1","status":"Blocked","hint":"… `quest task start SB-1 …` resumes it …"}]}}
```
What the docs say: `quest help doctor` describes a read-only consistency check
(`mutates: false`) and names no exit semantics for findings. The manifest defines exit 6
as `validationOrDrift`, and `quest agents --check` uses it for drift. So `doctor` behaves
as documented. It is not a defect. But a caller that branches on the exit code, as the
machine contract advises, treats an unhealthy workspace as healthy.

Suggested fix: a `--check` flag that exits 6 when `healthy` is false. Until then, callers
must read `data.healthy`. `lore orphans` has the same shape: it exits 0 with findings.

### (d) Test suites leak temp dirs in `$TMPDIR`

| Field | Value |
|---|---|
| Owners | lore-cli (`lore-readme-*`, `lore-check-package-artifacts-*`); opum-cli-e2e (`opum-e2e-ws-*`, `opum-e2e-platform-*`) |
| Version | The suites as run by agents during September 2026; not pinned to one release |
| Workflow step | Running the test and e2e suites, locally and by agents |
| Classification | Defect |

Minimal repro (count only; nothing removed):
```
ls "$TMPDIR" | grep -c '^lore-readme-'                     # 6303
ls "$TMPDIR" | grep -c '^lore-check-package-artifacts-'    # 4584
ls "$TMPDIR" | grep -c '^opum-e2e-ws-'                     # 1585
ls "$TMPDIR" | grep -c '^opum-e2e-platform-'               # 1186
du -sh "$TMPDIR"                                           # 24G
```
Exit code: 0 for every command; the suites themselves pass, which is why nobody sees it.
Single `opum-e2e-ws-*` dirs reach 970 MB. `$TMPDIR` held 27,559 entries, and 1,881 were
older than 7 days.

What should happen: a test removes the temp dirs it creates, in a `finally` or teardown,
including on failure. macOS purges `$TMPDIR` only for items untouched for about three days
(https://developer.apple.com/forums/thread/71382), and that did not catch these. Nothing
in Claude Code's `cleanupPeriodDays` sweep covers them
(https://code.claude.com/docs/en/claude-directory).

Suggested fix: wrap each `mkdtemp` in teardown that always runs, and add a CI assertion
that the suite leaves `$TMPDIR` as it found it. This plugin can only clear these at Deep
through configured `[tmp] prefixes`, which treats the symptom.

### (e) Orphaned `quest browser --port 0` processes

| Field | Value |
|---|---|
| Owner | quest-cli |
| Version | Binaries from 9 release-candidate installs plus the global install |
| Workflow step | Tests or agents that start `quest browser` and never stop it |
| Classification | Missing capability |

Minimal repro (inspection only):
```
ps -axo pid,ppid,etime,command | grep '[q]uest browser --port 0'
lsof -nP -iTCP -sTCP:LISTEN | grep quest
```
Exit code: 0. Actual state: **16** `quest browser --port 0 --json` processes with
**PPID 1**, each holding a `127.0.0.1` listener on a port between 50740 and 65001. Elapsed
times ranged from 1d17h to **9d23h**.

What the docs say: `browser` "Start[s] a local read-only web server showing the overview
and board". No lifetime, idle timeout, or shutdown behaviour is documented. A
`--port 0 --json` launch looks like a harness asking for an ephemeral server, which then
lost its parent.

Suggested fix: exit when the parent dies or stdin closes, or offer an `--idle-timeout`.
Also audit whichever tests start it with `--port 0`.

### (f) The opum-quest plugin installs about 620 MB per version

| Field | Value |
|---|---|
| Owner | quest-cli (plugin packaging) |
| Version | opum-quest 0.10.0; also 0.5.0 and 0.7.1 still in cache |
| Workflow step | Plugin install and every version bump |
| Classification | Defect |

Minimal repro:
```
du -sh ~/.claude/plugins/cache/opum/opum-quest/*/                  # ~620M each; 1.8G total
du -sh ~/.claude/plugins/cache/opum/opum-quest/0.10.0/{npm,node_modules}
```
Exit code: 0. Actual state: `npm/` is 497 MB of quest binaries for six platforms
(darwin-arm64, darwin-x64, linux-x64, linux-arm64, win32-x64, win32-arm64). `node_modules/`
is 107 MB, including biome and the TypeScript native compiler, which are development tools.

What should happen: a plugin ships what it needs at runtime. The whole repo is shipped as
the plugin, so each bump costs about 620 MB until Claude Code sweeps the orphaned version.
That sweep is slow in practice; see
[State of the art, section 5](state-of-the-art-in-agentic-housekeeping.md#5-claude-codes-built-in-hygiene-surface).

Suggested fix: publish the plugin from a subdirectory or a release artifact holding only
skills and manifest, and resolve the quest binary from the user's install.

### (g) `.claude/handovers/` files accumulate unpruned

| Field | Value |
|---|---|
| Owner | opum-fleet (opum-workflow plugin: `opum-handoff`, `flush-state.sh`) |
| Version | opum-workflow 0.10.8 |
| Workflow step | Session start, compaction and session end hooks; handoff writes |
| Classification | Missing capability |

Minimal repro (count only):
```
for d in <repos>/*/.claude/handovers; do printf '%s %s\n' "$(ls "$d" | wc -l)" "$d"; done | sort -rn
```
Exit code: 0. Actual state: 17 repos have the directory, all untracked. opum-agent holds
**130** files (520 KB) written since 2026-09-15, about 8.7 a day. Next: opum-cli-e2e 63,
opum-doc 51, lore-cli 48, quest-cli 45, opum-fleet 39.

What the docs say: `opum-handoff` keeps `cursor.md` and per-session
`running-plugin-root.<SESSION_ID>` markers there, and the directory is gitignored
fleet-wide. Nothing describes pruning. Which of the 130 files are session markers was not
broken down.

Suggested fix: remove a session's marker at SessionEnd, or prune markers whose session is
no longer live at SessionStart. This plugin reports them but never mutates another repo's
tree (ADR-0005).

### (h) commit-commands `/clean_gone` deletes on `[gone]` alone

| Field | Value |
|---|---|
| Owner | anthropics/claude-code and anthropics/claude-plugins-official (commit-commands) |
| Version | `main` as of 2026-09-26; the file is byte-identical in both repos |
| Workflow step | Post-merge branch and worktree pruning |
| Classification | Defect (loss of unlanded work); also missing capability (no dry run) |

Source: https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/commit-commands/commands/clean_gone.md.
Not installed or executed here. The repro below follows from the command text.

Minimal repro:
1. Push branch `b`, then add one more local commit to it.
2. Delete the remote branch without merging it.
3. Run `/clean_gone`.

`git branch -v` shows `b` as `[gone]`, and the command runs `git branch -D b`. The unpushed
commit is gone. If a worktree has `b` checked out with uncommitted edits,
`git worktree remove --force` deletes them first. No dry run is offered, and no SHA is
recorded for undo.

Other flaws:
- No `git fetch --prune` first, so `[gone]` may be stale.
- `grep '\[gone\]'` over `git branch -v` also matches a commit subject containing
  "[gone]".

What should happen: git-trim's README states "Just `gone` doesn't mean it is fully merged
to the base" (https://github.com/foriequal0/git-trim). Git's own `-d` refuses unmerged
branches; the command reaches for `-D` (https://git-scm.com/docs/git-branch).

Suggested fix: fetch with `--prune`; require a containment proof (ancestry, squash
equivalence, or a merged PR) before `-D`; drop `--force` on worktrees with changes; add a
dry run and print deleted SHAs. This plugin's
[R-5](../specs/cleanliness-levels.md#r-5-a-branch-with-unique-commits-is-unlanded-work-not-clutter)
is the rule it follows instead.

### (i) skill-creator trigger evals collide across parallel workers

- **Owner:** Anthropic's `skill-creator` plugin (claude-plugins-official). **Tool:**
  `scripts/run_eval.py`, cache version `fa59bc903774`, run with Python 3.12 and Claude
  Code 2.1.283.
- **Classification:** defect. **Workflow step:** description optimization and trigger
  evaluation (`run_eval.py`, and `run_loop.py`, which calls it).

Minimal repro:
1. Run `python -m scripts.run_eval --eval-set <8 should-fire queries> --skill-path <skill> --num-workers 8`.
2. While it runs, `ls .claude/commands/` shows 8 files `<skill>-skill-<uuid>.md` with
   identical descriptions.
3. Each `claude -p` sees all 8. Detection returns True only when the invoked command name
   contains the run's own uuid.

Observed (exit 0): the `tidy` skill scored 0/5 on its should-fire queries (trigger rates
0.0 to 0.33).

What should happen: a single probe with one copy installed invoked the skill as its first
tool call. Rerunning the same queries with one private project directory per run
(`evals/triggers.py` in this repo) scored 12/12 for `tidy` and 51/52 across all six
skills.

Suggested fix: give each `run_single_query` a private project root (a temporary directory
containing `.claude/commands/`), or run the workers serially.

