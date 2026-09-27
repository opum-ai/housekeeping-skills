---
# yaml-language-server: $schema=../../.lore/schemas/reference.schema.json
type: Reference
title: State of the art in agentic housekeeping
tags:
  - research
  - housekeeping
summary: "September 2026 survey of housekeeping for coding agents: prior art, git, files, runtime, Claude Code built-ins, incidents, SDD reconciliation, risk tiers, and a measured machine snapshot."
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:10.063Z
---

# State of the art in agentic housekeeping

Research carried out on 2026-09-26, in five passes:
- web prior art (skills, plugins, git, files, runtime, incidents, SDD, autonomy tiers);
- the reference skills installed locally (`opum-sdlc`, `opum-handoff`, commit-commands);
- the quest 0.10.0 and lore 0.9.3 CLI surfaces, run in a throwaway sandbox;
- Claude Code's built-in hygiene surface, checked against the installed `claude` 2.1.283;
- a read-only inventory of one developer machine.

Every external claim carries its source URL. A claim taken from a third-party write-up
rather than primary docs is marked *(secondary)*. The machine numbers are a dated
snapshot. Home paths are shown as `~`, user ids as `<uid>`, and repositories outside the
Opum fleet are anonymised. Upstream defects found along the way are listed separately in
[Upstream findings](upstream-findings.md).

## Details

### Conclusions that drive the design

1. **Nobody ships a complete housekeeping suite.** Anthropic's official plugins offer
   `/commit`, `/commit-push-pr` and `/clean_gone`. `anthropics/skills` has no git or cleanup
   skill. The best single skill is obra/superpowers' `finishing-a-development-branch`.
   Everything else is scattered community commands.
2. **Agent tools use the weak version of branch pruning.** git-trim, gh-poi and git-town
   know that "upstream gone" is not "merged". `/clean_gone` treats `[gone]` as safe, then
   runs `git branch -D` and `git worktree remove --force` with no dry run.
3. **The platform owns part of the job.** Claude Code, Codex and Cursor manage their own
   worktrees and transcripts. A plugin should clean what they leave behind, not duplicate
   them.
4. **The auto-mode classifier shapes the design.** It blocks deletion by glob or age in
   shared temp dirs, `rm -rf "$VAR"` with an unseen value, and teardown of resources Claude
   did not create. Housekeeping must resolve every target to a literal, named item.
5. **Cleanup is where the worst agent incidents happen.** Several `rm -rf $HOME` reports
   from 2025-2026 happened during "cleanup" or "test cleanup".
6. **Provenance changes what is permitted.** Auto mode allows "deleting the exact jobs
   Claude created earlier in the same session". A record of what the session created turns
   a risky guess into an approvable action.
7. **Post-implementation reconciliation is one-way.** spec-kit, OpenSpec, Kiro and BMAD
   bring code or tasks into line with the spec. None records an intentional deviation back.
8. **The measured debris is mostly outside the repo.** On the surveyed machine, session
   scratchpads (25 GB) and leaked test temp dirs (24 GB) dwarf in-repo build outputs, and
   no built-in sweep covers the second.

### 1. Prior art: skills, plugins and commands

| Prior art | What it does | Flaw or limit | Source |
|---|---|---|---|
| commit-commands `/commit` | Injects `git status`, diff and log; makes one commit | "Avoids committing secrets" is prompt-only; no scanner runs | https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/commit-commands/commands/commit.md |
| commit-commands `/commit-push-pr` | Branch, commit, push, `gh pr create` in one message | Allowed-tools names `git checkout --branch`, not a real git option | https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/commit-commands/commands/commit-push-pr.md |
| commit-commands `/clean_gone` | Greps `git branch -v` for `[gone]`; force-removes worktrees; `git branch -D` | See the list below | https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/commit-commands/commands/clean_gone.md |
| claude-md-management | `/revise-claude-md` captures session learnings into CLAUDE.md | Docs only; no git, runtime or disk | https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/claude-md-management/README.md |
| superpowers `finishing-a-development-branch` | Green suite gate; merge, PR or keep; typed `discard`; removes only worktrees it owns | One branch only; no estate sweep, no squash detection, no runtime or caches | https://raw.githubusercontent.com/obra/superpowers/main/skills/finishing-a-development-branch/SKILL.md |
| git-worktree-clean skill | Merged, unmerged or protected worktrees; `--dry-run` | Ancestry test only, so squash merges look unmerged | https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/examples/skills/git-worktree-clean/SKILL.md |
| beads "Landing the Plane" | File issues, gates, push, `git stash clear`, hand off | Unconditional `stash clear` destroys work; mandatory push ignores review policy | https://raw.githubusercontent.com/steveyegge/beads/main/AGENTS.md |
| cctop | TUI of sessions, process trees and orphan ports; SIGTERM with confirm | Ports only; reads `~/.claude` and the process table | https://github.com/stefanprodan/cctop |
| claude-code-cleaner | TUI over 13 `~/.claude` categories; protects settings and credentials | Harness only; interactive, not agent-driven | https://github.com/garrickz2/claude-code-cleaner |
| Handoff skills | Decisions, running state, next steps written at session end | Record only; no clearing | https://github.com/David-E-Kay/claude-session-handoff |

`/clean_gone` is byte-identical in `anthropics/claude-code` and
`anthropics/claude-plugins-official`. Its flaws:
1. No `git fetch --prune` first, so `[gone]` is only as fresh as the last prune.
2. `grep '\[gone\]'` over `git branch -v` also matches a commit *subject* containing "[gone]".
3. It treats "upstream gone" as safe. git-trim's README warns "Just `gone` doesn't mean it
   is fully merged to the base" (https://github.com/foriequal0/git-trim).
4. `-D` and `--force` run unconditionally, which destroys uncommitted work in a worktree.
5. No dry run, no confirmation, and no record of deleted SHAs for undo.

Other agents contribute patterns rather than suites:

| Agent | Pattern | Source |
|---|---|---|
| Aider | Reversibility by commit granularity; `/undo`. `--git-commit-verify` defaults off, so secret-scan hooks are skipped | https://aider.chat/docs/git.html |
| Codex app | Snapshot before deleting a managed worktree; offers restore | https://learn.chatgpt.com/docs/environments/git-worktrees |
| Cursor | Periodic worktree cleanup that also deletes worktrees it did *not* create | https://cursor.com/docs/configuration/worktrees |
| Copilot cloud agent | Namespaced `copilot/` branches; cannot push to the default branch | https://docs.github.com/en/copilot/responsible-use/copilot-cloud-agent |
| Devin | No branch cleanup; users add workflows that delete `devin/` heads on PR close | https://github.com/VibeBB/wire-agent/pull/53 |

The local reference skill `opum-sdlc` (opum-workflow 0.10.8) already encodes the strongest
branch rule seen anywhere: "A branch with unique commits is unlanded work, not clutter…
This is the only irreversible mistake." It proves squash merges by PR state plus
`git merge-base --is-ancestor <mergeCommit> origin/dev`. Its estate audit (`sdlc-audit`)
adds tree equality via `git merge-tree --write-tree`. It deliberately automates "the
refusal, never the destruction".

**Implication for this plugin.** Borrow superpowers' ownership scoping and typed
confirmation, Codex's snapshot-before-delete, and `opum-sdlc`'s containment proofs. Never
copy `/clean_gone`'s gone-equals-safe rule. Cover the domains no prior art covers: runtime,
caches, harness debris and docs, under one gate.

### 2. Git hygiene

#### 2.1 Proving a branch landed

`git branch --merged` is ancestry-only (https://git-scm.com/docs/git-branch). Squash and
rebase merges give the landed commit a new SHA, so ancestry misses them.

| Proof | Catches | Misses | Source |
|---|---|---|---|
| Ancestry: `merge-base --is-ancestor`, `branch --merged` | Merge commits, fast-forwards | Squash, rebase | https://git-scm.com/docs/git-branch |
| Patch-id: `git cherry` | Rebase merges | Multi-commit squashes | https://github.com/foriequal0/git-trim |
| Synthetic squash: `commit-tree` of the branch tree on the merge-base, then `git cherry` | Squashes | Squashes edited after review | https://github.com/foriequal0/git-trim, https://stackoverflow.com/a/56026209 |
| Tree equality: `git merge-tree --write-tree` of branch onto trunk equals trunk's tree | Squashes, edited-then-landed content | Conflicting branches | `sdlc-audit` in opum-agent (local reference) |
| Forge PR state: `MERGED` PR whose merge commit is on the trunk | Any merge style | Branches never PR'd | https://github.com/seachicken/gh-poi |

Tools that get this right:
- **git-trim** classifies branches as *merged* or *stray*: "there is a chance to lose some
  changes if you delete it". It has `--dry-run` (https://github.com/foriequal0/git-trim).
- **gh-poi** uses GitHub PR state, handles squashes, and `gh poi lock` protects a branch
  (https://github.com/seachicken/gh-poi).
- **git-town** deletes gone branches only with "no unshipped changes", and
  `git town undo` reverses the last command (https://www.git-town.com/commands/sync,
  https://www.git-town.com/commands/undo).
- **git-gone**'s canonical one-liner, `git branch -vv | awk '/: gone]/{print $1}' | xargs git branch -D`,
  is exactly the unsafe pattern (https://github.com/eed3si9n/git-gone).

A deleted branch stays recoverable from its SHA until gc prunes unreachable objects
(`gc.pruneExpire` default two weeks; https://git-scm.com/docs/git-gc). Recording the
branch→SHA map makes deletion undoable with `git branch <name> <sha>`.

#### 2.2 Worktrees, stashes, refs and pushes

- **Worktrees.** `git worktree remove` refuses unclean worktrees without `--force`; a
  locked one needs `--force` twice. `list --porcelain` shows `locked` and `prunable`
  (https://git-scm.com/docs/git-worktree).
- **Stashes.** A dropped stash is recoverable only through `git fsck` until gc, and
  "dropping the stash takes [its reflog] with it"
  (https://dev.to/thebguy/recovering-a-dropped-stash-what-git-fsck-can-still-find-50g9)
  *(secondary)*.
- **Tags.** `--prune-tags` can "delete all your local tags, most of which may not have come
  from the `<name>` remote" (https://git-scm.com/docs/git-fetch).
- **Force push.** Bare `--force-with-lease` "interacts very badly with anything that
  implicitly runs git fetch". Prefer `--force-with-lease=<ref>:<expect>` plus
  `--force-if-includes` (https://git-scm.com/docs/git-push).
- **Secrets.** `gitleaks git --pre-commit --redact --staged` is the current hook entry
  (https://github.com/gitleaks/gitleaks). Official `/commit` relies on the prompt alone.

**Implication for this plugin.** A branch is removable only on a containment proof, after
a fresh `fetch --prune`, and never on "upstream gone". Record every deleted SHA. Export
stashes before dropping them. Never prune tags by default. This is spec R-5.

### 3. Files, build outputs and caches

| Tool | What it removes | Safety features | Source |
|---|---|---|---|
| kondo | Artifact dirs across 20+ ecosystems | Interactive, `--dry-run`, `--older` | https://github.com/tbillington/kondo |
| npkill | `node_modules` | Flags system dirs, `--dry-run`, `--exclude-sensitive` | https://github.com/voidcosmos/npkill |
| cargo-sweep | Old `target/` artifacts | `--time`, `--maxsize`, `--dry-run` | https://github.com/holmgr/cargo-sweep |
| uv | `uv cache prune` | "it's never safe to modify the cache directly" | https://docs.astral.sh/uv/concepts/cache/ |
| pnpm | `pnpm store prune` | Removes only packages no project uses | https://pnpm.io/cli/store |
| npm | `npm cache clean --force` | Deliberate friction; cache is self-healing | https://docs.npmjs.com/cli/v11/commands/npm-cache |
| Gradle | Auto-cleans the user home by age | Built in | https://docs.gradle.org/current/userguide/directory_layout.html |

`git clean` is the wrong tool for "clean build artifacts" (https://git-scm.com/docs/git-clean):
- `-x` removes *all* untracked files, including new unstaged source.
- `-X` removes only ignored files. That includes `.env`, `.env.local`,
  `.claude/settings.local.json` and local databases: files ignored because they are
  *local*, not because they are *disposable*.

Deletion itself has no undo inside the harness. "Checkpointing does not track files
modified by Bash commands" (https://code.claude.com/docs/en/checkpointing). macOS 15 ships
`/usr/bin/trash`, though Finder's "Put Back" does not work for it
(https://mjtsai.com/blog/2025/08/26/the-trash-command/). trash-cli implements the
FreeDesktop spec on Linux (https://github.com/andreafrancia/trash-cli).

The synthesized safe-deletion pattern:
1. Enumerate candidates as literal absolute paths, resolved without following symlinks.
2. Assert containment under an allowed root.
3. Match an *allowlist* of regenerable directory names per ecosystem.
4. Show a plan table: path, size, age, reason, reversibility.
5. Move to trash where possible; otherwise delete only regenerable content.
6. Log what was removed. Never delete through a generated script.

**Implication for this plugin.** Build outputs are chosen by ecosystem allowlist, never by
`git clean -X`. Caches are pruned by their own official commands. Files go to trash by
default. This is spec R-6 and the S2 class.

### 4. Containers and processes

- **Docker prune is host-global.** `docker system prune` removes all stopped containers,
  unused networks, dangling images and build cache on the host, whatever project owns them.
  "By default, volumes aren't removed to prevent important data from being deleted"
  (https://github.com/docker/cli/blob/master/docs/reference/commandline/system_prune.md).
- **Compose is project-scoped.** `docker compose down` keeps external networks and volumes;
  `-v` also removes named volumes declared in the file; `--dry-run` exists
  (https://github.com/docker/compose/blob/main/docs/reference/compose_down.md). The label
  `com.docker.compose.project=<name>` scopes everything else.
- **Background processes outlive sessions.** Processes started by the Bash tool "are not
  cleaned up when the session ends… reparented to PID 1"; orphaned `next dev` servers reach
  "8+ GB each". The issue was closed as not planned. Port-based cleanup hooks "kill
  user-started processes (false positives)"
  (https://github.com/anthropics/claude-code/issues/43944). Related:
  https://github.com/anthropics/claude-code/issues/9780 (duplicate dev servers on one port).
  Community reports include 37+ orphans using 6 GB+ on macOS
  (https://github.com/anthropics/claude-code/issues/33947,
  https://github.com/anthropics/claude-code/issues/50544).
- **Discovery primitives.** `lsof -iTCP -sTCP:LISTEN` for listeners
  (https://man7.org/linux/man-pages/man8/lsof.8.html); `kill -- -PGID` for a process group
  (https://man7.org/linux/man-pages/man1/kill.1.html).

**Implication for this plugin.** Scope containers by Compose label or working directory,
never by a host-wide prune below C5. Kill only processes the ledger or the repo's working
directory attributes, with SIGTERM before SIGKILL. Hard-protect named infrastructure such as
a self-hosted CI runner in every Docker context.

### 5. Claude Code's built-in hygiene surface

Checked against the installed `claude` 2.1.283 on 2026-09-26, plus the docs cited.

| Command | What it does | Mutates? | Source |
|---|---|---|---|
| `claude doctor` | Installation health, settings parse, plugin and MCP errors, permission rules, hook syntax | No | https://code.claude.com/docs/en/troubleshooting |
| `/doctor` (in session) | The same, plus unused extensions, CLAUDE.md bloat, slow hooks, allowlist bloat; applies fixes after confirmation | Yes, user-invoked | https://code.claude.com/docs/en/debug-your-config |
| `claude project purge [path] [--all] [--dry-run] [-i]` | Deletes a project's transcripts, tasks, file history and config entry | Yes; has `--dry-run` | https://code.claude.com/docs/en/sessions |
| `claude plugin details <name>` | Component inventory and projected always-on token cost | No | https://code.claude.com/docs/en/plugins/install |
| `claude plugin list \| disable \| uninstall \| prune \| validate` | List; disable; uninstall; remove auto-installed dependencies no longer needed; validate a manifest | `disable`, `uninstall`, `prune` do | https://code.claude.com/docs/en/plugins/install |
| `claude agents`, `claude rm <id>` | List background agents; delete a background session (its transcript stays resumable) | `rm` does | https://code.claude.com/docs/en/sessions |
| `claude mcp list \| remove` | List or remove MCP servers | `remove` does | https://code.claude.com/docs/en/mcp |

`claude doctor` points users to `/doctor` "for a full checkup that can also fix issues".
A slash command is user-invoked, so a skill can recommend `/doctor` but cannot run it.

**`cleanupPeriodDays`** (default 30, minimum 1) drives a sweep at session start
(https://code.claude.com/docs/en/claude-directory, https://code.claude.com/docs/en/sessions).

| Swept after the period | Never swept |
|---|---|
| Transcripts and subagent transcripts, `tool-results/`, `file-history/` (keeps 100), plans, debug logs, paste cache, `session-env/`, tasks, shell snapshots, `.trash` dirs | `history.jsonl` (every typed prompt), `stats-cache.json`, `cache/changelog.md` |
| Session scratchpads, removed with their transcript | Auto-memory (`projects/*/memory/`), removed only if empty |
| `.claude.json` backups beyond the newest 5 | `$TMPDIR` entries created by commands the agent ran |
| Clean, marked subagent and background worktrees | Worktrees made with `git worktree add`, and worktrees from `-p` runs |

Orphaned plugin versions are handled separately. They are marked `.orphaned_at` and
reportedly swept after about 14 days. A request for `claude plugin gc` was closed as not
planned (https://github.com/anthropics/claude-code/issues/47966), and stale `.in_use`
markers can make Claude resolve outdated plugin content
(https://github.com/anthropics/claude-code/issues/95420).

**Worktrees.** Claude Code writes a provenance marker into every worktree it creates, and
"the sweep keeps any worktree without one". Non-interactive (`-p`) runs get no cleanup, and
their lock stays until a stale-lock sweep (https://code.claude.com/docs/en/worktrees).

**SessionEnd hooks** "can't block session termination". They have a **1.5 s default
timeout**, and "timeouts set on plugin-provided hooks don't raise the budget"
(https://code.claude.com/docs/en/hooks).

**Skill frontmatter.** `disable-model-invocation: true` prevents auto-triggering;
`allowed-tools` pre-approves tools only for the invoking turn
(https://code.claude.com/docs/en/skills).

**Implication for this plugin.** Call the built-ins, do not reimplement them: `claude doctor`
as an S0 probe, `claude project purge --dry-run` before any transcript purge (S3), and
`claude plugin details` for context-cost ranking. Cover the gaps the sweep leaves: `$TMPDIR`,
user-made worktrees, `-p` worktrees, orphaned plugin versions, memory staleness. Heavy work
cannot run in a SessionEnd hook; it has to be a skill the user runs before exit.

### 6. Auto-mode classifier constraints

Auto mode has been the built-in default since v2.1.283. A classifier reviews each action
(https://code.claude.com/docs/en/permission-modes).

| Blocked by default | Allowed by default |
|---|---|
| "Irreversibly destroying files that existed before the session" | Local file operations in the working directory |
| Force push; `git reset --hard`, `git checkout -- .`, `git restore .`, `git clean -fd`, `git stash drop`, `git stash clear` | Pushing to the working repo's branches |
| "Deleting files in /tmp, $TMPDIR, or another shared scratch or cache directory by wildcard, glob, or age filter rather than by a specific named path" | "Deleting the exact jobs Claude created earlier in the same session" |
| "Deleting or tearing down a stateful resource Claude didn't create in the session", unless the user named it | |
| `rm -rf "$VAR"` when the value is not visible in the conversation | |
| Merging a pull request no human has approved | |

Approval must "name the action and its specifics", and covers one action unless granted as
standing. Three consecutive blocks, or 20 in total, pause auto mode. `rm` on critical paths
cannot be allow-listed at all.

**Implication for this plugin.** Write skills *for* the classifier. Every deletion names its
literal target. Every S3 confirmation names the item. The engine never emits a glob, an
age filter, or an unresolved variable. Ledger provenance is what makes a teardown fall under
"exact jobs Claude created".

### 7. Agent incidents during cleanup

| Date | What happened | Source |
|---|---|---|
| 2026-09-03 | `rm -rf "$HOME"` "during test cleanup" after HOME was restored from a temp value; 68,550 deletions in auto mode | https://github.com/anthropics/claude-code/issues/93099 |
| 2026 | A trap `rm -rf "$_HT_HOME"` with late expansion and a later reassignment deleted `$HOME`; the permission check saw only `bash /tmp/…/test-lib-demo.sh`; the "5th report of this class" | https://github.com/anthropics/claude-code/issues/88462 |
| 2025 | "Clean up packages" produced `rm -rf tests/ patches/ plan/ ~/` | https://github.com/anthropics/claude-code/issues/10077, https://www.docker.com/blog/coding-agent-horror-stories-the-rm-rf-incident/ |
| 2025-07 | Replit's agent deleted a production database during a code freeze | https://incidentdatabase.ai/cite/1152/ |
| 2025 | Gemini CLI moves overwrote files after a failed `mkdir`, with no read-after-write check | https://incidentdatabase.ai/cite/1178/ |

The common cause is a deletion whose target was computed, not stated, and executed by a
script the permission layer could not see into.

**Implication for this plugin.** Deletion lives in one audited engine, never in generated
shell. Targets are resolved and containment-checked before planning, re-checked before
applying, and journalled. This is ADR-0003.

### 8. Session closure and post-implementation reconciliation

- **Land the plane.** beads' checklist: file issues, run gates, update status, push, verify
  clean, hand off. "Work is NOT complete until `git push` succeeds"
  (https://raw.githubusercontent.com/steveyegge/beads/main/AGENTS.md).
- **Clean state.** Anthropic's harness guidance asks each session to leave "code suitable
  for merging to main" and a progress record
  (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).
- **spec-kit `/speckit.converge`** "never edits or deletes code, and its only possible
  write is adding tasks to tasks.md" (https://github.com/github/spec-kit).
- **OpenSpec** `/opsx:sync` merges delta specs into the main specs; `/opsx:archive` moves a
  change to `changes/archive/` (https://github.com/Fission-AI/OpenSpec).
- **Kiro** "Sync Files" creates tasks for new requirements and marks completed ones
  (https://kiro.dev/docs/specs/).
- **BMAD** epic retrospectives find "spec divergence", but `correct-course` rewrites the
  criteria of completed stories and breaks traceability
  (https://docs.bmad-method.org/build/finish-an-epic/,
  https://github.com/bmad-code-org/BMAD-METHOD/issues/1930).

Each of these reconciles in one direction. None classifies a divergence as "code is wrong",
"spec is stale", or "intentional deviation, record it and supersede".

**Implication for this plugin.** Record before clearing, and land before clearing (spec
R-1). `session-sync` reconciles in both directions and makes a per-item decision: fix
code, amend the spec, or record a deviation. Mandatory push and stash policy are
configurable, not hard-coded.

### 9. Autonomy and risk tiering

- **Levels of autonomy.** Feng, McDonald and Zhang define L1 Operator to L5 Observer; L4
  Approver engages the user "where they require a green-light in specified risk scenarios".
  Autonomy is "a deliberate design decision, separate from capability"
  (https://arxiv.org/abs/2506.12469).
- **OWASP LLM06 Excessive Agency.** "Do not rely on the LLM to decide whether an action is
  authorized"; enforce authorization downstream
  (https://owasp.org/www-project-top-10-for-large-language-model-applications/2_0_vulns/LLM06_ExcessiveAgency.html).
- **Plan then apply.** `terraform apply` of a saved plan "executes exactly those changes"
  (https://developer.hashicorp.com/terraform/cli/commands/plan).
- **Codex CLI** crosses a sandbox tier with an approval policy
  (https://developers.openai.com/codex/concepts/sandboxing).

| Mechanism | Prior art |
|---|---|
| Dry run | git-trim, gh-poi, git-town, kondo, npkill, `git clean -n`, `compose down --dry-run` |
| Apply exactly the reviewed plan | Terraform plan files |
| Typed confirmation | superpowers `discard` |
| Protected lists and locks | `trim.bases`, `gh poi lock`, `git worktree lock`, rulesets |
| Snapshot or undo | Codex snapshots, `git town undo`, Aider `/undo`, reflog |
| Provenance scoping | Claude Code worktree marker, `copilot/` prefixes, Docker labels |

No surveyed tool combines a shared risk class, blast radius, provenance and an undo journal
across git, files, containers and processes.

**Implication for this plugin.** Two dials: the cleanliness level sets reach, and the safety
class gates each operation. Evidence only ever raises a class. Authorization lives in the
engine, not in the model's judgement. This is the spec's S0-S3 model.

### 10. Measured machine inventory (snapshot, 2026-09-26)

One developer machine (macOS, 10 days of uptime), measured read-only. The oldest transcript
was 22 days old, so everything below accumulated in about three weeks, before the 30-day
sweep had removed anything. These are observations, not benchmarks.

| Area | Measured | Notes |
|---|---|---|
| Session scratchpads `/private/tmp/claude-<uid>/` | **25 GB**, 583 sessions | 293 `.git` dirs inside; single scratchpads of 1.1-1.2 GB |
| `$TMPDIR` | **24 GB**, 27,559 entries | Leaked test and e2e temp dirs; 1,881 older than 7 days despite the macOS purge |
| `~/.claude/` | 4.4 GB | `plugins/` 2.39 GB, `projects/` 1.70 GB |
| Plugin cache | 2.43 GB in 43 version dirs | 42 orphaned versions = 1.76 GB (73%); 718 of 731 `.in_use` PIDs dead |
| Transcripts | 2,220 files | 55% from headless evals or a watchdog; 9 of 27 project dirs point at deleted paths |
| Shell snapshots | 349 in 2 days, 95 MB | Documented as "removed on clean exit", so many exits were unclean |
| Auto-memory | largest index 126 lines / 22.6 KB | About 90% of the loader's byte cap; 27 memories self-mark as superseded |
| Processes | 16 orphaned `quest browser --port 0` | PPID 1, up to 9d23h old, each holding a localhost port |
| Docker | 10.0 GB reclaimable images, 7.7 GB build cache | 2 dangling volumes (543 MB); the CI runner container lives in another context |
| Repos | 20 `node_modules` = 4.7 GB, 10 `.venv` = 1.4 GB | 1.7 GB in repos idle 60+ days |
| Worktrees | lore-cli: 7 linked, about 1.25 GB | 4 under `$TMPDIR` made with `git worktree add`, invisible to Claude's sweep; 1 locked, 1 dirty |
| Handover markers | 130 untracked in opum-agent in 11 days | 17 repos affected; never pruned |
| Instructions | CLAUDE.md up to 875 lines / 52 KB | 11 repos exceed the ~200-line guidance |
| Permissions | 15 one-off rules at user scope | One stale repo has 100 allow rules, including `rm *` and `bash *` |
| Global dev caches | `~/.npm` 13 GB, `~/.cache/uv` 2.5 GB | Regenerable |
| Junk signature | `~/nul` | An agent ran a Windows `2>nul` redirect on macOS |

How the top targets map to the spec's levels and classes:

| Target | Level | Class | Why |
|---|---|---|---|
| This session's junk, processes and clean worktrees | C2 | S1 | The ledger proves provenance |
| Orphaned processes attributed to the repo | C3 | S1, or S3 when unattributed | A port alone does not prove ownership |
| Prunable worktrees; this project's stopped containers | C3 | S1 | Git and Compose prove scope |
| Orphaned plugin versions; old scratchpads; attributed `$TMPDIR` prefixes | C4 | S2 | Regenerable, but outside the repo |
| Project images and networks; volumes | C4 | S2; volumes S3 | Volumes hold unique data |
| Transcripts of deleted project paths | C4 | S3 | `claude project purge --dry-run` first |
| CLAUDE.md, memory, permission and hook bloat | C4 | proposals only | Applied only on approval |
| Global caches; machine-wide Docker minus the protected set | C5 | S2; volumes S3 | Official prune commands |
| Other repos' worktrees, handovers and debris | never mutated | reported | ADR-0005 |

**Implication for this plugin.** The largest piles are harness and temp debris, not repo
content, so harness-hygiene and workspace-clean carry most of the reclaimed bytes. Several
piles are caused by other tools' defects. Those belong upstream; see
[Upstream findings](upstream-findings.md).

### 11. Commodity and novel

Commodity, to wrap and not reinvent:
- conventional commits; commit, push and PR;
- `git worktree prune`; cache prune commands; kondo-style artifact discovery;
- CLAUDE.md revision; handoff notes; Claude-managed worktrees; gitleaks.

Solved outside agents but unused inside them:
- squash-aware branch classification with PR state;
- lease-guarded force pushes;
- label-scoped container cleanup;
- undo logs.

Open ground this plugin occupies:
1. A provenance ledger of what the session created.
2. One safety-class engine and plan format across git, files, runtime and harness, with a
   journal and undo.
3. A leveled "land the plane" orchestrator, configurable per repo.
4. Two-way spec, tracker and docs reconciliation.
5. Agent-junk detection cross-checked against provenance rather than names alone.
6. Housekeeping written to pass the published auto-mode rules.

**Implication for this plugin.** Spend effort on items 1-6. Everywhere else, call the
existing tool and add only the gate.
