# Claude Code setup audit: prioritized cleanup list

Scope: `CLAUDE_CONFIG_DIR=…/fixture/claude-home` and the project `…/fixture/repo`.
Method: I followed the `harness-hygiene` skill. I ran the engine's read-only survey
(`hk plan --level C4 --domains harness`) and read every settings, memory and CLAUDE.md file it flagged.
I made no cleanup changes. The saved plan is at `outputs/harness-plan.json`.

Paths used below:

```bash
export FX=<workspace>/iteration-1/eval-harness-audit/with_skill/run-1/fixture
export CLAUDE_CONFIG_DIR=$FX/claude-home
export HK="python3 <repo>/scripts/hk.py"
export PLAN=$FX/../outputs/harness-plan.json
export MEM="$CLAUDE_CONFIG_DIR/projects/-private-tmp-claude-501--Volumes-external-repos-housekeeping-skills-88482b1c-3570-4612-a5d0-34d34963c60a-scratchpad-hk-workspace-iteration-1-eval-harness-audit-with-skill-run-1-fixture-repo/memory"
```

## Priority 1: permission allowlist (risk: these rules approve actions without asking you)

Of the 9 allow rules in `claude-home/settings.json`, 8 are flagged (finding `har-195cf106`):

| Rule(s) | Problem | Proposal |
|---|---|---|
| 6 rules: `Bash(gh api -X PUT repos/acme/{api,web,cli,docs,infra,sdk}/rulesets/*)` | The same rule repeated once per repo. Each one is a standing approval to **write remote state** (branch-protection rulesets). | Drop all 6 if the rulesets rollout is finished. If it isn't, use one rule, `Bash(gh api -X PUT repos/acme/*/rulesets/*)`, and remove it when the rollout ends. |
| `Bash(rm:*)` | Far too broad: it auto-approves any `rm`, including `rm -rf` anywhere. | Drop it. If you want a narrow rule, allow only the exact paths you routinely remove. |
| `Read(…/fixture/nonexistent-dir/**)` | Points at a directory that no longer exists. | Drop it. |
| `Bash(npm test)` | Fine. | Keep it. |

The proposed result is `"allow": ["Bash(npm test)"]`. Once you approve, the command is:

```bash
cp "$CLAUDE_CONFIG_DIR/settings.json" "$CLAUDE_CONFIG_DIR/settings.json.bak"
jq '.permissions.allow = ["Bash(npm test)"]' "$CLAUDE_CONFIG_DIR/settings.json" > /tmp/s.json \
  && mv /tmp/s.json "$CLAUDE_CONFIG_DIR/settings.json"
```

You can also run `/permissions` in a session and delete the rules there.

## Priority 2: always-loaded context bloat (cost: paid on every turn of every session)

1. **`repo/CLAUDE.md` is 420 lines** (guideline is 300 or fewer; finding `har-bf521dbb`). It is
   420 uniform bullets ("Rule 0: always do thing 0 carefully." through "Rule 419") with no
   sections and no managed blocks. From the file alone I can't tell which rules you need every
   session and which only matter sometimes, so the triage is yours.
   - **Proposal:** keep the always-needed rules in CLAUDE.md, aiming for roughly 50 lines.
   - Move the rest into `repo/docs/agent-rules.md`, or into nested `CLAUDE.md` files in the
     subdirectories they concern, and link to them from a one-line pointer in CLAUDE.md.
   - Expected change: 420 lines down to about 50.
   - Once you say which rules are core, I'll draft the diff.
2. **The auto-memory `MEMORY.md` is 190 lines** (guideline is 150 or fewer; finding `har-c56f0e4f`).
   It is worse than long: **all 190 index entries point at `note0.md` … `note189.md`, and none of
   those files exist.** The memory dir contains only `MEMORY.md` and `old-deploy.md`. The whole
   index is dead pointers that cost context every session.
   - **Proposal:** rewrite MEMORY.md so it indexes only files that exist.
   - After item 3 below, nothing is left to index, so the file becomes empty or a header.

```bash
ls "$MEM"                                    # confirms: MEMORY.md old-deploy.md only
cp "$MEM/MEMORY.md" "$MEM/MEMORY.md.bak" && : > "$MEM/MEMORY.md"   # after approval
```

## Priority 3: superseded memory (risk: stale guidance keeps steering the agent)

- **`memory/old-deploy.md`** says "Deploy with make ship. SUPERSEDED by the release workflow."
  (finding `har-18f195d9`).
- No successor memory exists to fold it into, and it isn't even listed in MEMORY.md.
- **Recommendation:** delete it. If the release-workflow facts matter, write a fresh memory for
  them instead.

```bash
mv "$MEM/old-deploy.md" ~/.local/share/housekeeping-trash/   # or rm, after approval
```

## Priority 4: plugin cache (S2: regenerable, one batch approval)

| id | Item | Why |
|---|---|---|
| `har-157b353a` | `plugins/cache/acme/widget/1.0.0` (8 KB) | Claude Code marked it orphaned (`.orphaned_at` = 1780000000000, about four months ago) but never deleted it. Version 1.1.0 is present. |
| `har-74dfc962` | `plugins/cache/acme/widget/1.1.0/.in_use/999991`, `999992` | In-use markers from PIDs that are not running (`ps` finds neither). Stale markers can pin an outdated plugin version (anthropics/claude-code #95420). |

```bash
$HK apply "$PLAN" --approve-s2        # runs exactly those two S2 items; journaled, see `$HK undo`
```

## Priority 5: transcripts for a project whose folder is gone (S3: irreversible)

- `projects/-gone-project/0a1b.jsonl` records `cwd = …/fixture/deleted-project`, and that
  directory no longer exists (item `har-61a2341b`).
- **Caveat, found by dry-run:** the engine plans this item as
  `claude project purge $FX/deleted-project -y`, but that command won't find the data.
  - I ran `CLAUDE_CONFIG_DIR=$FX/claude-home claude project purge $FX/deleted-project --dry-run`.
    It replied "No Claude Code project state found for …/deleted-project".
  - The transcript folder is named `-gone-project`, not the slug Claude Code derives from that
    path.
  - So `$HK apply "$PLAN" --confirm har-61a2341b` would effectively do nothing.
  - **Don't rely on it.**
- **Recommendation:** if nothing in that transcript matters, remove the folder directly. If it
  might matter, first `claude --resume` the session and `/export` it.

```bash
ls -la "$CLAUDE_CONFIG_DIR/projects/-gone-project"                       # review first
mv "$CLAUDE_CONFIG_DIR/projects/-gone-project" ~/.local/share/housekeeping-trash/   # after approval
```

## Also worth running (read-only, or user-run)

- Run `claude doctor` (terminal), and `/doctor` and `/context` inside a session.
  - `/doctor` can apply the CLAUDE.md-bloat and allowlist-consolidation fixes itself.
  - `/context` shows the token cost of what is loaded.
- `CLAUDE_CONFIG_DIR=$FX/claude-home claude plugin list` and `claude mcp list`.
  - The fixture has no `installed_plugins.json`, and no MCP servers or hooks configured, so there
    was nothing to rank there.
  - No duplicate skills: the repo has no `.claude/skills`.
- `cleanupPeriodDays` isn't set, so the 30-day default already expires old transcripts for
  **existing** projects. It will not remove the gone project, the memory, the CLAUDE.md or the
  orphaned plugin version above.

## Side effect to be aware of

My `claude project purge --dry-run` check (which runs Claude Code against your config dir) created
first-start bootstrap files in `claude-home`: `.claude.json` and
`backups/.claude.json.backup.1790480854554`, both timestamped 22:47 during this audit. They
weren't there before. I tried to remove them to leave the directory as I found it, but the
sandbox's permission guard blocked the deletion, so they are still there. They're harmless.
Delete them if you want the dir exactly as it was:

```bash
rm "$CLAUDE_CONFIG_DIR/.claude.json" "$CLAUDE_CONFIG_DIR/backups/.claude.json.backup.1790480854554" && rmdir "$CLAUDE_CONFIG_DIR/backups"
```
