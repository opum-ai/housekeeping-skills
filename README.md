# housekeeping-skills

**Housekeeping for agentic engineering, at the level of clean you ask for.** Six Claude
Code skills and a small deterministic engine that clean up after coding agents safely:
- record progress in the tracker and docs;
- land the work in git;
- prune what is provably landed;
- clear junk, build outputs, caches, containers, and orphaned processes;
- keep the Claude Code harness itself lean.

The reach runs from the daily chores to a clean-room deep scrub.

**Status:** v0.1.0. Owned by [Opum AI](https://github.com/opum-ai), MIT licensed. It has
native support for [quest](https://github.com/opum-ai/quest-cli) (tasks) and
[lore](https://github.com/opum-ai/lore-cli) (docs), and defers to `opum-sdlc` for branch
policy when that skill is installed.

## Why

Coding agents leave things behind:
- branches and worktrees;
- `*_v2.py` and `.bak` files, and `IMPLEMENTATION_SUMMARY.md`;
- temp dirs from test runs;
- dev servers that outlive the session;
- stale memories, and one-off permission rules.

The tools that exist either do too little (commit and PR helpers) or too much, too
bluntly. The official `/clean_gone` treats "upstream gone" as proof of merge, and
force-removes worktrees without checking them for uncommitted work. Cleanup is also where
the worst agent incidents happen: two recent `rm -rf $HOME` cases came from test cleanup
scripts.

This plugin separates **how far** a pass reaches from **how each operation is gated**:
- it proves before it deletes;
- it applies exactly the plan a person saw;
- it keeps an undo journal.

## Cleanliness levels

| Level | Name | Adds |
|---|---|---|
| **C1** | **Tidy** | Tracker progress note, logical commits on the task branch, push. Nothing is removed. |
| **C2** | **Sweep** | This session's junk files, processes, and clean worktrees; the docs it touched; stash review. |
| **C3** | **Clean** (task done) | Close the task in its PR, merge, prune landed branches (local and remote), worktrees, stale refs, this project's containers, orphaned processes in the repo; tracker/docs gates. |
| **C4** | **Deep clean** | Build outputs, dependency dirs, project caches and images, old stashes, stale unlanded branches (archived first), `$TMPDIR` leaks, old session scratchpads, Claude Code harness debris and bloat. |
| **C5** | **Clean room** | Checkout reset to fresh-clone state (minus a keep-list), global caches, machine Docker, then **prove it rebuilds from scratch** and certify what remains. |

Every pass runs **record → land → clear → verify → report**. Recording comes first
because clearing can destroy the evidence a record needs.

Other repositories' working trees are reported, never changed, at any level. Each repo
has one live session that owns it.

## Safety classes: independent of the level

| Class | Meaning | Gate |
|---|---|---|
| S0 | read-only | none |
| S1 | reversible; the undo is journalled (trash, archive ref, stop) | runs within the level |
| S2 | regenerable at a cost (build outputs, caches, images) | one batch approval |
| S3 | irreversible (unlanded commits, volumes, unknown untracked files, transcripts) | confirmed **per item, by name** |

Evidence raises a class and nothing lowers it. A junk-named file that no session is
recorded as creating is S2, not S1.

The **protected set** is never planned, at any level:
- trunk and release branches, `retain/*`, `preserve/*`, `archive/*`;
- `.env*`, keys, tracked files, `.quest/`, `.lore/`, `docs/`;
- the self-hosted CI runner;
- the current session's scratchpad.

**A branch with unique commits is unlanded work, not clutter.** A branch is removable
only on a containment proof:
- **ancestry**;
- **squash-merge equivalence** (`git merge-tree --write-tree` equals trunk's tree);
- **a merged PR** whose merge commit is in trunk.

"Upstream gone" is evidence, not proof.

## The skills

| Skill | Role |
|---|---|
| **`tidy`** | The orchestrator. Picks the level from context ("wrap up" → C1, "PR merged" → C3, "deep clean" → C4), runs the phases in order, gates by class, and writes the report (and, at C5, the clean-room certificate). |
| **`session-sync`** | Record. Quest progress notes, criteria checked only with evidence, `quest task complete` with a final summary citing the PR and CI run, follow-up tasks, `lore sync`/`check`, and two-way spec-drift reconciliation (fix the code, amend the spec, or record a deviation). |
| **`git-hygiene`** | Land and prune. Logical commits (no junk, no secrets), push, PR, merge, and promote (per `opum-sdlc`, or a generic flow); landed-branch, worktree, stash, and ref pruning through the engine. |
| **`workspace-clean`** | Agent junk, `$TMPDIR` leaks (and their cause), build and dependency outputs, scratchpads, and clean-room resets. Never `git clean -X`. |
| **`runtime-clean`** | Dev servers and orphaned processes the repo owns; this project's containers, images, networks, and volumes; build cache. Never the CI runner or someone's live terminal. |
| **`harness-hygiene`** | Claude Code itself: `claude doctor`, transcripts of deleted projects (`claude project purge`), orphaned plugin versions and dead in-use markers, memory and CLAUDE.md bloat, one-off permission rule families, duplicate skills, hooks, MCP servers, background agents. |

## The engine: `hk`

`scripts/hk.py` is stdlib-only Python 3.9+.

```text
hk status              landing state: branch, trunk, ahead/behind, quest In Progress (+scope), lore check, open PRs
hk inventory           everything found up to a level, classified (read-only)
hk plan --level C3     a reviewable plan: items by class, findings, notes; saved as JSON
hk apply <plan>        executes exactly the plan: re-checks fingerprints (drift -> skipped), S2 needs
                       --approve-s2, S3 needs --confirm <id>; trash by default; journals every action
hk undo <journal>      reverses S1 actions (branches, stashes, worktrees, trashed files, stopped containers)
hk ledger add|show     the provenance ledger
hk doctor              which tools are available (git, gh, docker, quest, lore, claude, trash)
```

Every command takes `--json` and returns the `{schemaVersion, kind, data}` envelope.
Exit codes:
- `0`: ok;
- `2`: usage;
- `3`: not found;
- `5`: drift (an item changed since planning);
- `6`: findings or failures.

**Provenance (opt-in).**
1. Set `[provenance] enabled = true` in `.housekeeping.toml`.
2. The plugin's fail-open hook then records what each session creates: new files,
   branches, worktrees, containers, and background commands.
3. Cleanup can target exactly those items. Anything else is raised a class and shown for
   review.

## Install

```text
/plugin marketplace add opum-ai/opum-marketplace
/plugin install housekeeping-skills@opum
```

Optional: copy `housekeeping.example.toml` to `.housekeeping.toml` at a repo's root to
set level defaults, protected branches, paths, and containers, temp prefixes your tests
leak, clean-room keep and verify commands, and provenance capture.

## Usage

Say it in words, or use the command. `/clean` takes the level as its argument:

```text
/clean tidy        C1: note, logical commits, push
/clean sweep       C2
/clean done        C3: close the task, merge, prune landed branches
/clean deep        C4
/clean room        C5: clean room + rebuild proof
/clean deep audit  read-only: show the C4 plan, change nothing
/clean             infer the level from context
```

Or just ask:

```text
> wrap up for today                                  (C1: note, commits, push)
> clean up after yourself                            (C2)
> PR merged, close out HS-4 and tidy the branches    (C3)
> my disk is full, deep clean but ask before anything scary   (C4)
> make this repo a clean room before the release     (C5 + rebuild proof)
> port 3000 is in use and nothing should be running
> audit my Claude Code setup: plugins, memory, permissions
```

## Evaluation

See [the evaluation story](docs/stories/skill-evaluation-suite.md) and `evals/`. The
graders inspect the resulting repository and filesystem state, never the agent's own
report. Fixtures use a bare remote with branches in every containment state, so pushes,
merges, and pruning behave as they do against a real host.

Results: see the table below (updated per benchmark iteration).

<!-- benchmark:begin -->
**Iteration 1** (2026-09-26, claude-opus-5-5; `evals/benchmarks/iteration-1/`). 5 task evals, with vs without the
plugin, graded on the resulting repo/filesystem state:

| | With skills | Without |
|---|---|---|
| Assertion pass rate | **100%** (47/47) | 95.6% (45/47) |
| Time | 138 s ± 44 | 93 s ± 20 |
| Tokens | 61.9k ± 11.2k | 45.7k ± 6.3k |

An honest reading:
- **The baseline is strong.** Opus 5.5 without the plugin already keeps `feat/gone`, spots
  `parser_v2.py` as real work, and leaves a false acceptance criterion unchecked. The
  difference is two assertions: the landed *remote* branch deleted, and separate logical
  commits.
- **What the skills add that the assertions don't capture:**
  - an undo journal for every removal;
  - the level and the reason, stated;
  - a follow-up task that carries an unmet criterion.
- **Iteration 1 was most useful for the engine defects it exposed**, all fixed:
  - state leaking into the repo;
  - a two-pass worktree branch;
  - a `claude project purge` slug mismatch.
- **Iteration 2 needs harder, more discriminating cases.**

**Triggering: 51/52** should-fire and near-miss queries passed, 3 runs each, each run in an isolated project dir (see
`evals/triggers.py`):

| Skill | Passed |
|---|---|
| `tidy` | 12/12 |
| `git-hygiene` | 7/8 |
| `session-sync` | 8/8 |
| `workspace-clean` | 8/8 |
| `runtime-clean` | 8/8 |
| `harness-hygiene` | 8/8 |

The one miss, "promote dev to main", is taken by `opum-sdlc` when it is installed, which is the intended owner of
promotion (ADR-0002). Bare "tidy up" and "time for a deep clean" trigger `tidy` 3/3.
<!-- benchmark:end -->

## Development

```bash
uv venv --python /usr/bin/python3 .venv && uv pip install --python .venv/bin/python pytest
.venv/bin/python -m pytest tests -q           # engine and hook tests
claude plugin validate . && lore check        # plugin manifest and docs gate
```

The docs bundle under `docs/` is driven with `lore`, and tasks with `quest` (prefix `HS`).
The design of record is [docs/specs/cleanliness-levels.md](docs/specs/cleanliness-levels.md).
