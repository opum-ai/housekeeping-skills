# housekeeping-skills

**Project housekeeping for agentic engineering, at the level you ask for.** Six Claude
Code skills and a small deterministic engine that clean up after coding agents safely:
- record progress in the tracker and docs;
- land the work in git;
- prune what is provably landed;
- clear junk, build outputs, caches, containers, and orphaned processes;
- keep the Claude Code harness itself lean.

The levels run from saving a recoverable stopping point to an immaculate, fully accounted-for
project. They cover housekeeping only (commits, branches, caches, containers, issue
statuses, docs, and handoffs), not improving the code itself.

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

This plugin keeps three things separate: **how much** housekeeping (the level), **where** (the scope), and **how each operation is gated** (its safety class):
- it proves before it deletes;
- it applies exactly the plan a person saw;
- it keeps an undo journal.

## Housekeeping levels

| Level | Name | Meaning |
|---|---|---|
| **1** | **Minimal** | Preserve the work and record where things stand: a recoverable stopping point. |
| **2** | **Light** | Put away what you just used: commit completed work, update the immediate issue, remove task-generated temp files. |
| **3** | **Standard** (default) | The routine checklist: reconcile commits and issue statuses, update docs and handoff notes, remove known disposable artifacts (landed branches, this project's stopped containers, reviewed junk). |
| **4** | **Deep** | The places routine housekeeping misses: stale branches and worktrees, disposable caches and build outputs, outdated statuses, obsolete docs, leftover artifacts, Claude Code debris. |
| **5** | **Immaculate** | Deep, **plus verify the final state**. Every in-scope change, branch, issue, doc, and artifact has an intentional disposition. |

**Immaculate means nothing left unattended, not nothing left on disk.** A kept `.env`, a
`retain/` branch, or a task deferred to a follow-up is immaculate, as long as its
disposition is stated. `hk disposition` checks this, and exits 0 only when nothing is
unaccounted for.

**Scope is a separate setting:**
- `session`: only what this session created;
- `repo` (the default): this repository and this project's containers, processes, and
  Claude Code state;
- `machine`: adds global caches, all of Docker, the plugin cache, and deleted projects'
  transcripts.

A deeper level never widens the scope: deep-cleaning the kitchen does not authorize
remodeling the house. Other repositories' working trees are reported, never changed, in
any scope.

Every pass runs **record → land → clear → verify → report**. Recording comes first
because clearing can destroy the evidence a record needs.

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
| **`tidy`** | The orchestrator, also run by `/clean`. Picks the level and scope from context ("save where we are" → Minimal, "wrap up for today" → Light, "tidy up" or "PR merged" → Standard, "deep clean" → Deep, "leave it immaculate" → Immaculate). Runs the phases in order, gates by class, and writes the report; at Immaculate, it also writes the disposition record. |
| **`session-sync`** | Record. Quest progress notes, criteria checked only with evidence, `quest task complete` with a final summary citing the PR and CI run, follow-up tasks, `lore sync`/`check`, and two-way spec-drift reconciliation (fix the code, amend the spec, or record a deviation). |
| **`git-hygiene`** | Land and prune. Logical commits (no junk, no secrets), push, PR, merge, and promote (per `opum-sdlc`, or a generic flow); landed-branch, worktree, stash, and ref pruning through the engine. |
| **`workspace-clean`** | Agent junk, `$TMPDIR` leaks (and their cause), build and dependency outputs, scratchpads, and Immaculate dispositions for leftovers. Never `git clean -X`. |
| **`runtime-clean`** | Dev servers and orphaned processes the repo owns; this project's containers, images, networks, and volumes; build cache. Never the CI runner or someone's live terminal. |
| **`harness-hygiene`** | Claude Code itself: `claude doctor`, transcripts of deleted projects (`claude project purge`), orphaned plugin versions and dead in-use markers, memory and CLAUDE.md bloat, one-off permission rule families, duplicate skills, hooks, MCP servers, background agents. |

## The engine: `hk`

`scripts/hk.py` is stdlib-only Python 3.9+.

```text
hk status              landing state: branch, trunk, ahead/behind, quest In Progress (+scope), lore check, open PRs
hk inventory           everything found up to a level, classified (read-only)
hk plan --level standard --scope repo   a reviewable plan: items by class, findings, notes
hk disposition --level immaculate       every in-scope item and its disposition; exit 0 = nothing unaccounted
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
leak, Immaculate keep-list and verify commands, and provenance capture.

## Usage

Say it in words, or use the command. `/clean` takes the level as its argument:

```text
/clean minimal           save a recoverable stopping point
/clean light             put away what you just used (wrap-up)
/clean                   Standard: the routine checklist (the default)
/clean deep              the places routine housekeeping misses (this repo)
/clean deep machine      ... including global caches, all Docker, ~/.claude
/clean immaculate        Deep, plus a verified disposition for everything in scope
/clean deep audit        read-only: show the Deep plan, change nothing
```

Or just ask:

```text
> save where we are, context is almost full          (Minimal)
> wrap up for today                                  (Light)
> tidy up / PR merged, close out HS-4               (Standard)
> deep clean this repo, ask before anything scary   (Deep)
> leave it immaculate for the handover              (Immaculate)
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
**Iteration 2** (2026-09-27, claude-opus-5-5, Minimal..Immaculate; `evals/benchmarks/iteration-2/`). 8 task evals, with
vs without the plugin, 3 runs per configuration on the three new, harder cases; graded on the resulting repo, remote,
filesystem and process state:

| | With skills | Without |
|---|---|---|
| Assertion pass rate | **98.6%** | 88.9% |
| Time | 131 s ± 50 | 81 s ± 31 |
| Tokens | 62k ± 17k | 39k ± 13k |

| Case (runs) | With | Without | What differed |
|---|---|---|---|
| squash-estate: 8 squash-merged branches, a partially landed one, and a stale-looking unlanded one (3) | 14/15 | 13/15 | Every unblocked run deleted exactly the 8. Nobody deleted the partial branch or the spike. |
| immaculate-handover (3) | **21/21** | 19/21 | Only the skill runs produced a verified disposition for every leftover (`hk disposition` exit 0). |
| runtime-sandbox: an orphaned server in the repo plus a decoy server outside it (3) | **9/9** | 7/9 | The skill runs stopped only the repo's orphan, through `hk`. No run killed the decoy. |
| 5 iteration-1 cases (1) | 42/42 | 40/42 | The baseline kept a landed remote branch and mixed two concerns into one commit. |

**Read this before quoting the delta.** 7 of the 9 failed assertions are Claude Code
auto-mode classifier blocks: the harness refused a destructive command, and the agent
correctly stopped.
- **Baselines: 6 blocks,** on `git branch -D`, `rm`, and `kill`.
- **Skill runs: 1 block,** on `hk apply` itself.

The classifier examines the engine's single `hk apply` call less closely than it examines
each raw command, so the plugin relies on its own guards instead:
- containment proofs, fingerprints, per-class gates, and an undo journal;
- enforcement of **your own** permission rules on the equivalent command. A
  `permissions.deny` rule makes `hk apply` refuse the item. An `ask` rule or an auto-mode
  `soft_deny` rule (for example `Bash(git branch -D:*)`) makes it require a per-item
  confirmation.

If you want the harness to confirm every apply as well, add
`"ask": ["Bash(python3 *hk.py apply:*)"]` to your permissions.

**Triggering: 51/52** should-fire and near-miss queries, 3 runs each, each in an isolated
project dir (`evals/triggers.py`). Bare "tidy up" and "time for a deep clean" trigger
`tidy` 3/3. The one miss, "promote dev to main", goes to `opum-sdlc`, its intended owner.

Iteration 1 (C1–C5 draft, 5 cases): 100% vs 95.6%. See `evals/benchmarks/iteration-1/`.
<!-- benchmark:end -->

## Development

```bash
uv venv --python /usr/bin/python3 .venv && uv pip install --python .venv/bin/python pytest
.venv/bin/python -m pytest tests -q           # engine and hook tests
claude plugin validate . && lore check        # plugin manifest and docs gate
```

The docs bundle under `docs/` is driven with `lore`, and tasks with `quest` (prefix `HS`).
The design of record is [docs/specs/cleanliness-levels.md](docs/specs/cleanliness-levels.md).
