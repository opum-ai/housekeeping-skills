---
name: harness-hygiene
description: Keep the Claude Code harness itself clean - old sessions and transcripts (including projects whose folders no longer exist), auto-memory and CLAUDE.md bloat, stale or superseded memories, the plugin cache and unused or context-heavy plugins, duplicate skills, hooks, one-off or overly broad permission allowlist rules, MCP servers, background agents and scheduled tasks. Use this skill whenever the user says Claude feels slow or the context fills up fast, asks to clean up old sessions, prune memories, slim CLAUDE.md, review hooks or permissions, remove unused plugins or MCP servers, asks why ~/.claude or the plugin cache is so big, or asks for a Claude Code checkup or doctor pass - and at the Deep level of any housekeeping pass (user-wide items need machine scope).
---

# harness-hygiene

The harness is the agent's own workshop: instructions, memory, tools, permissions, and
history. When it gets cluttered, every session pays twice:
- in **context**: every always-loaded line and every skill description is read on every
  turn;
- in **behaviour**: stale memories and one-off permissions keep acting long after the
  situation that justified them is gone.

Claude Code already ships part of this job. Use its own tools first, and fill the gaps.
Don't reimplement them.

Engine: `hk() { python3 "<dir>/../../scripts/hk.py" "$@"; }   # a function: works in bash and zsh`, where `<dir>` is the
`Base directory for this skill` that the Skill tool printed. Verified command surface:
`references/claude-code-surface.md`.

## 1. Built-in checkup

```bash
claude doctor                        # read-only: install, settings validity, plugin/MCP errors
```

Recommend that the user run **`/doctor`** in a session for the full checkup. It can apply
fixes: unused extensions, CLAUDE.md bloat, slow hooks, allowlist consolidation. It is a
slash command: you cannot run it; suggest it. `cleanupPeriodDays` (default 30) already
expires old transcripts, file history, shell snapshots, and plans at startup. It does not
touch:
- memory, CLAUDE.md, or settings;
- projects whose directory is gone;
- plugin versions it marked orphaned but has not deleted;
- worktrees made with plain `git worktree add`.

That list is this skill's job.

## 2. Survey

```bash
hk plan --level deep --domains harness --chosen-by "…"               # this project: memory, CLAUDE.md, repo settings
hk plan --level deep --scope machine --domains harness --chosen-by "…"   # + plugin cache, deleted projects, user settings
claude plugin list
claude mcp list
```

| Kind | What | Class | Action |
|---|---|---|---|
| `plugin.orphaned-version` | plugin cache versions Claude Code marked orphaned | S2 | rm (protected while a live session uses one) |
| `plugin.stale-in-use` | in-use markers left by dead processes (they can pin an outdated plugin version) | S2 | rm the dead pids' markers |
| `project.missing-path` | transcripts, tasks, and file history of a project whose folder is gone | **S3** | `claude project purge <path> -y` |
| `scratchpad.old` | old session scratch dirs | S2 | rm (never the current session's) |
| `context.large-file` | CLAUDE.md > 300 lines, user CLAUDE.md > 200, MEMORY.md > 150 | finding | propose a slimmer version |
| `memory.superseded` | memory files that say they are superseded or obsolete | finding | propose a fold or delete |
| `settings.permission-rules` | allow rules that are one-off (a SHA, an issue URL, a deleted path), repeated families (the same rule per repo), overly broad (`Bash(rm:*)`, `mcp__*`), or standing approvals for writes to remote state | finding | propose a consolidated list |
| `settings.many-hooks` | > 10 hooks in one settings file | finding | review with `/hooks` |
| `skills.duplicate` | the same skill in the repo's `.claude/skills` and in a plugin | finding | keep one |

For `project.missing-path`, preview first with
`claude project purge <path> --dry-run`. If any transcript might matter, suggest
`/export` from a resumed session before purging.

## 3. Proposals: the user decides, you edit

Memory, CLAUDE.md, settings, and plugin choices encode someone's decisions. The engine
**reports** them and never edits them. Here is the flow for each:

- **CLAUDE.md / AGENTS.md.**
  1. Read it.
  2. Mark what is always-needed and what is situational.
  3. Propose moving the situational detail into a skill, a `references/` file, or a
     nested `CLAUDE.md` in the subdirectory it concerns.
  4. Show a before/after line count and the diff.
  5. Keep managed blocks (`<!-- quest:… -->`, `<!-- lore:… -->`) byte-for-byte. Their
     tools regenerate them.
- **Memory** (`~/.claude/projects/<project>/memory/`).
  1. Read MEMORY.md and the files it points to.
  2. For each candidate, check whether it still holds. Does the file, flag, or function
     it names still exist? Did a later memory supersede it?
  3. Propose, per memory: merge it into its successor, delete it, or keep it.
  4. Use AskUserQuestion, one question per batch of up to 4 memories, with a
     recommendation for each.
  5. Update the MEMORY.md index along with the files.
- **Permissions.**
  1. Group the flagged rules.
  2. Propose the replacement. For example, 17 per-repo `gh api … rulesets` rules become
     nothing (the rollout is over) or one pattern; drop rules for deleted paths; narrow
     `Bash(rm:*)`.
  3. Edit the settings file only after approval. If the `update-config` skill is
     available, use it.
- **Plugins.**
  1. Rank them with `claude plugin details <name>`, which reports the projected token
     cost.
  2. Ask the user which ones they actually use.
  3. Disabling (`claude plugin disable <name>`) is reversible, so prefer it to
     `uninstall`.
  4. `claude plugin prune` removes auto-installed dependencies nothing needs. It is S2:
     batch approval.
- **MCP servers.** `claude mcp list` shows the status. A server that has failed for weeks,
  or that nobody calls, costs tool-schema tokens on every turn. Propose
  `claude mcp remove <name>` with its scope, for the user to approve.
- **Hooks.** List them with `/hooks` (the user runs it) or read the settings files. Flag:
  - hooks without a timeout;
  - hooks that call the network on every tool use;
  - duplicates across the user, project, and plugin scopes;
  - SessionEnd hooks doing real work. They time out after about 1.5 s, so cleanup there
    silently doesn't happen. It belongs in a skill run before exit.
- **Background agents and schedules.** `claude agents` lists background sessions;
  `claude rm <id>` deletes one (its transcript stays resumable). Scheduled tasks and
  routines: list them (CronList, `/schedule`). Propose removing the ones whose purpose has
  passed.

## 4. Apply the engine's items

```bash
hk apply <plan.json> [--approve-s2] [--confirm <ids>]
```
- **S2** (orphaned plugin versions, dead markers, old scratchpads): one batch approval.
- **S3** (`claude project purge`): each project confirmed by name.

## Never

- Edit files under `~/.claude/plugins/cache` by hand, other than through `hk`'s
  orphaned-version and dead-marker items.
- Delete the current session's transcript or scratchpad.
- Change managed settings, or rewrite another tool's managed blocks.
- Disable a plugin or remove an MCP server the user didn't approve. A capability that
  "looks unused" to you may be the one they rely on weekly.
