# Claude Code hygiene surface (verified against Claude Code 2.1.283, 2026-09-26)

Run `claude <cmd> --help` for the installed version. Flags change between releases.

## Commands a skill can run (terminal)

| Command | What it does | Class |
|---|---|---|
| `claude doctor` | read-only health check: install, settings validity, plugin and MCP errors | S0 |
| `claude project purge [path] [--all] [--dry-run] [-i] [-y]` | deletes a project's transcripts, tasks, file history, and config entry | S3 (use `--dry-run` first) |
| `claude plugin list` | installed plugins | S0 |
| `claude plugin details <name>` | component inventory and **projected token cost** | S0 |
| `claude plugin disable\|enable <name>` | toggle without uninstalling | S1 |
| `claude plugin uninstall <name>` | remove it | S2 (reinstallable) |
| `claude plugin prune` (alias `autoremove`) | remove auto-installed dependencies nothing needs | S2 |
| `claude plugin validate <path>` | validate a plugin or marketplace manifest | S0 |
| `claude plugin marketplace …` | list, add, remove, or update marketplaces | S1 / S2 |
| `claude mcp list` / `claude mcp remove <name>` | MCP servers | S0 / S2 |
| `claude agents` | list background sessions | S0 |
| `claude rm <id>` | delete a background session (its transcript remains resumable) | S2 |
| `claude logs <id>` | recent output of a background session | S0 |

## Slash commands (the user runs these; suggest them)

- **`/doctor`**: the full checkup, and it can apply fixes:
  - unused skills, plugins, and MCP servers;
  - CLAUDE.md bloat;
  - slow hooks;
  - allowlist consolidation;
  - version currency.
- **`/context`**: what is loaded and what each part costs.
- **`/memory`**: memory file locations; toggle auto-memory.
- **`/hooks`**: active hooks, by event and scope.
- **`/permissions`**: the resolved allow and deny rules.
- **`/plugin`**: the plugin browser (including its Errors tab).
- **`/mcp`**: server status; reconnect or approve.
- **`/export`**: render the current transcript to a file before purging anything that
  matters.

## Retention that already exists

`cleanupPeriodDays` (settings; default 30, minimum 1) sweeps these at startup:
transcripts, subagent transcripts, tool-results, file-history (the newest 100 per
session), plans, tasks, shell snapshots, debug logs, image and paste caches, and
session-env.

It keeps:
- the 5 newest `.claude.json` backups;
- `history.jsonl`;
- `stats-cache.json`;
- memory directories;
- remote settings and policy caches.

Session scratchpads under `/private/tmp/claude-<uid>/<project>/<session>/` go when their
transcript expires.

Not handled by any built-in:
- plugin versions marked `.orphaned_at` but never deleted;
- stale `.in_use/<pid>` markers (anthropics/claude-code #95420);
- projects whose path is gone (until you purge them);
- memory and CLAUDE.md bloat;
- one-off allow rules;
- worktrees made with plain `git worktree add`, and `-p` run worktrees.

## Paths

| Path | Contents |
|---|---|
| `~/.claude/projects/<slug>/` | `<session>.jsonl` transcripts, `<session>/subagents/`, `<session>/tool-results/`, `memory/` (MEMORY.md and memory files) |
| `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` | installed plugin versions; `.orphaned_at`, `.in_use/<pid>` |
| `~/.claude/plugins/installed_plugins.json` | install paths per plugin |
| `~/.claude/settings.json`, `<repo>/.claude/settings.json`, `<repo>/.claude/settings.local.json` | user, project, and local settings: permissions, hooks, env |
| `~/.claude.json` | per-project state and history |
| `<repo>/.claude/worktrees/` | Claude-created worktrees (removed on exit when clean) |
