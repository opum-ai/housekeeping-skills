# Claude Code setup audit: prioritized cleanup list

I only looked. Nothing was changed, deleted or stopped. I did not read or touch anything outside the fixture (no `~/.claude`, no global caches, no processes outside the fixture).

To keep the commands readable, they use these variables. Set them first:

```sh
export CLAUDE_CONFIG_DIR=<workspace>/iteration-2/eval-harness-audit/without_skill/run-1/fixture/claude-home
FIX=<workspace>/iteration-2/eval-harness-audit/without_skill/run-1/fixture
REPO=$FIX/repo
PROJ_MEM="$CLAUDE_CONFIG_DIR/projects/-private-tmp-claude-501--Volumes-external-repos-housekeeping-skills-88482b1c-3570-4612-a5d0-34d34963c60a-scratchpad-hk-workspace-iteration-2-eval-harness-audit-without-skill-run-1-fixture-repo/memory"
```

Quit any Claude Code session that uses this config dir before you run them. The CLI rewrites `settings.json` and the plugin cache while it runs.

---

## Priority 1: Remove the blanket `Bash(rm:*)` permission (security)

`$CLAUDE_CONFIG_DIR/settings.json` has `"Bash(rm:*)"` in `permissions.allow`. Every `rm`, including `rm -rf` on any path, runs without asking you. This is the riskiest item on the list. Change 2 below removes it together with the other dead rules.

## Priority 2: Prune the rest of the user-level permission list

| Rule | Finding | Recommendation |
|---|---|---|
| 6 x `Bash(gh api -X PUT repos/acme/{api,web,cli,docs,infra,sdk}/rulesets/*)` | These are write operations that change branch-protection rulesets. The six entries differ only in the repo name, so they look left over from a one-time rollout. | Remove them if the rollout is finished. If you still need them, replace them with one rule such as `Bash(gh api -X PUT repos/acme/*/rulesets/*)`. Check in `/permissions` that the wildcard matches the way you expect. |
| `Read(.../fixture/nonexistent-dir/**)` | The directory does not exist, so the rule never matches anything. | Remove it. |
| `Bash(npm test)` | Harmless and narrow. | Keep it. |

**Change 2**: back up the file, then remove `rm:*`, the dead Read rule and the six ruleset rules. I tested this filter on a scratch copy and the result is `["Bash(npm test)"]`.

```sh
cp "$CLAUDE_CONFIG_DIR/settings.json" "$CLAUDE_CONFIG_DIR/settings.json.bak"
jq --arg dead "Read($FIX/nonexistent-dir/**)" \
  '.permissions.allow |= map(select(. != "Bash(rm:*)" and . != $dead
     and (test("^Bash\\(gh api -X PUT repos/acme/[^/]+/rulesets/\\*\\)$") | not)))' \
  "$CLAUDE_CONFIG_DIR/settings.json.bak" > "$CLAUDE_CONFIG_DIR/settings.json"
```

If you want to keep one ruleset rule instead of dropping all six, run this afterwards:

```sh
jq '.permissions.allow += ["Bash(gh api -X PUT repos/acme/*/rulesets/*)"]' "$CLAUDE_CONFIG_DIR/settings.json" > /tmp/s.json && mv /tmp/s.json "$CLAUDE_CONFIG_DIR/settings.json"
```

## Priority 3: Project `CLAUDE.md` is bloated and untracked

`$REPO/CLAUDE.md` is 420 lines (17.8 KB), and every line looks like `- Rule N: always do thing N carefully.` It loads into context at the start of every session in this repo, uses tokens, and dilutes any instruction that actually matters. Anthropic recommends keeping CLAUDE.md short (roughly under 200 lines).

It is also **untracked** (`git status` lists `?? CLAUDE.md`, and it is not in `.gitignore`), so git cannot restore it if you delete it. Back it up before you edit it.

```sh
cp "$REPO/CLAUDE.md" "$REPO/../CLAUDE.md.bak-$(date +%Y%m%d)"
# Then rewrite it by hand to the few rules that matter, e.g.:
$EDITOR "$REPO/CLAUDE.md"
```

When it is trimmed, decide whether it belongs in git:

```sh
git -C "$REPO" add CLAUDE.md && git -C "$REPO" commit -m "Add trimmed CLAUDE.md"   # share it with the team
# or keep it personal: rename to CLAUDE.local.md and ignore it
mv "$REPO/CLAUDE.md" "$REPO/CLAUDE.local.md"
echo "CLAUDE.local.md" >> "$REPO/.gitignore"
```

I can't tell which of the 420 "rules" you actually want, so rewriting the content is your call.

## Priority 4: Auto-memory for the repo is broken and nearly at its load limit

In `$PROJ_MEM`:

- `MEMORY.md` has **190 index lines**. All of them link to `note0.md` through `note189.md`, and **none of those files exist**, so every entry is a dead link. Claude Code loads only about the first 200 lines of `MEMORY.md`, so this index takes up almost the whole budget and holds nothing useful.
- `old-deploy.md` is not listed in the index, and its own text says it is superseded: "Deploy with make ship. SUPERSEDED by the release workflow." It is stale guidance that could mislead a future session.

```sh
cp -R "$PROJ_MEM" "$PROJ_MEM.bak-$(date +%Y%m%d)"
rm "$PROJ_MEM/old-deploy.md"
: > "$PROJ_MEM/MEMORY.md"      # empty the index (every entry is dangling)
```

To confirm the links are dead first:

```sh
grep -o '([^)]*\.md)' "$PROJ_MEM/MEMORY.md" | tr -d '()' | while read f; do [ -e "$PROJ_MEM/$f" ] || echo "missing: $f"; done | wc -l   # expect 190
```

## Priority 5: Orphaned transcript for a deleted project

`$CLAUDE_CONFIG_DIR/projects/...-fixture-deleted-project/0a1b.jsonl` belongs to `$FIX/deleted-project`, which no longer exists. It is small (231 bytes), but it is dead history, and it clutters `/resume` and any audit.

```sh
rm -rf "$CLAUDE_CONFIG_DIR/projects/-private-tmp-claude-501--Volumes-external-repos-housekeeping-skills-88482b1c-3570-4612-a5d0-34d34963c60a-scratchpad-hk-workspace-iteration-2-eval-harness-audit-without-skill-run-1-fixture-deleted-project"
```

(Skip this if you want to keep that conversation. It is the only copy.)

## Priority 6: Orphaned plugin version in the cache

- `plugins/cache/acme/widget/1.0.0` has `.orphaned_at = 1780000000000`, which is 2026-05-28, about 4 months ago. It has been replaced by 1.1.0 and is safe to remove. Claude Code normally garbage-collects orphaned versions on its own, so this one has been left behind.
- `plugins/cache/acme/widget/1.1.0` is the current version. **Keep it.** Its `.in_use/999991` and `.in_use/999992` markers point to PIDs that cannot exist (`ps` reports "process id too large"), so they are stale locks. They are harmless. Remove them only while no Claude Code session is running, and doing so is optional.

```sh
rm -rf "$CLAUDE_CONFIG_DIR/plugins/cache/acme/widget/1.0.0"
# optional, only with Claude Code fully quit:
rm -f "$CLAUDE_CONFIG_DIR/plugins/cache/acme/widget/1.1.0/.in_use/999991" "$CLAUDE_CONFIG_DIR/plugins/cache/acme/widget/1.1.0/.in_use/999992"
```

---

## Checked and clean (no action needed)

- **Git repo** (`$REPO`): on `dev`. Local `dev` and `main` both point at `b71833f` and match `origin/dev` and `origin/main`. There are no stashes, no extra worktrees, no unmerged or stale branches, and no loose-object garbage (6 objects, 24 KiB). The only untracked file is `CLAUDE.md` (Priority 3).
- **`.claude.json`**: `{"projects": {}}`, with no stale project entries.
- **Processes**: no process has a working directory under the fixture, so there is nothing to stop.
- **Hooks**: the repo only has git's default `*.sample` hooks. No Claude Code hooks are configured in `settings.json`.

## Left for you to decide

- What `CLAUDE.md` should actually say, and whether to commit it or keep it local (Priority 3).
- Whether the six `acme/*/rulesets` permissions are still needed, and in which form (Priority 2).
- Whether the `deleted-project` transcript is worth keeping (Priority 5).
