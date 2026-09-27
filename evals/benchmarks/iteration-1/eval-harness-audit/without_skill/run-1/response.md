# Claude Code setup audit: what to clean up

I only read files. Nothing was changed, moved or deleted. This file is the only thing I wrote.

**What I checked**
- `CLAUDE_CONFIG_DIR`: `.../fixture/claude-home`. This covers `settings.json`, `projects/` (transcripts and memory) and `plugins/cache/`.
- Project: `.../fixture/repo`. This covers `CLAUDE.md`, `.gitignore`, and the git branches, remotes, stashes and worktrees.

## Setup (paste once; every command below uses these)

```sh
FIX=<workspace>/iteration-1/eval-harness-audit/without_skill/run-1/fixture
export CLAUDE_CONFIG_DIR="$FIX/claude-home"
REPO="$FIX/repo"
PROJ="$CLAUDE_CONFIG_DIR/projects/-private-tmp-claude-501--Volumes-external-repos-housekeeping-skills-88482b1c-3570-4612-a5d0-34d34963c60a-scratchpad-hk-workspace-iteration-1-eval-harness-audit-without-skill-run-1-fixture-repo"
BAK="$FIX/.hk-backup-$(date +%Y%m%d-%H%M%S)"   # everything is moved here, not rm'd, so every step can be undone
mkdir -p "$BAK"
```

Close any running Claude Code sessions that use this config dir first. Claude Code rewrites `settings.json` and the memory files while it runs.

---

## P0: security

### 1. `Bash(rm:*)` is on the global allow list
`claude-home/settings.json` pre-approves **any** `rm` command, in any project, with any flags. That includes `rm -rf` on paths outside the repo. This is the riskiest item in the setup. Remove it, and let `rm` ask for approval each time. If you need it pre-approved, add narrow project-scoped rules instead, such as `Bash(rm -rf dist)`.

```sh
cp "$CLAUDE_CONFIG_DIR/settings.json" "$BAK/settings.json"
jq '.permissions.allow -= ["Bash(rm:*)"]' "$CLAUDE_CONFIG_DIR/settings.json" > "$CLAUDE_CONFIG_DIR/settings.json.tmp" \
  && mv "$CLAUDE_CONFIG_DIR/settings.json.tmp" "$CLAUDE_CONFIG_DIR/settings.json"
```

---

## P1: files loaded into every session's context (token cost)

### 2. Project `CLAUDE.md` is 420 lines / 17.8 KB of generic filler
`repo/CLAUDE.md` holds 420 near-identical lines ("Rule N: always do thing N carefully"). Nothing in it is specific to this project. All of it is loaded into every session in this repo. The file is also **untracked** in git: it isn't committed and isn't ignored.

Recommendation: replace it with a short, project-specific file (build/test commands, conventions, gotchas; well under ~100 lines). Then decide one of two options:
- Commit it (shared with the team).
- Rename it to `CLAUDE.local.md` and ignore that file (just for you).

I can't tell which of the 420 rules you actually rely on, so what goes into the new file is your call.

```sh
# back up the current file, then start a minimal one
mv "$REPO/CLAUDE.md" "$BAK/CLAUDE.md"
cat > "$REPO/CLAUDE.md" <<'EOF'
# Demo

A small demo project.

## Conventions
- (add only rules that are specific to this repo and that Claude gets wrong without them)
EOF

# Then EITHER share it:
git -C "$REPO" add CLAUDE.md && git -C "$REPO" commit -m "Add trimmed CLAUDE.md"
# OR keep it personal:
# mv "$REPO/CLAUDE.md" "$REPO/CLAUDE.local.md" && echo "CLAUDE.local.md" >> "$REPO/.gitignore"
```

### 3. Auto-memory index `MEMORY.md` points at 190 notes that don't exist
`$PROJ/memory/MEMORY.md` has 190 entries (`[Note 0](note0.md)` … `[Note 189](note189.md)`, 6.9 KB). **None** of those `noteN.md` files exist. The index is dead weight that still gets loaded at session start. It is also close to the ~200-line point where Claude Code stops reading the index.

```sh
mv "$PROJ/memory/MEMORY.md" "$BAK/MEMORY.md"
: > "$PROJ/memory/MEMORY.md"      # empty index; Claude Code will rebuild it as it saves real memories
```

### 4. Superseded memory file `old-deploy.md`
`$PROJ/memory/old-deploy.md` says "Deploy with make ship. SUPERSEDED by the release workflow." It is stale by its own label and isn't listed in the index.

```sh
mv "$PROJ/memory/old-deploy.md" "$BAK/old-deploy.md"
```

---

## P2: stale configuration

### 5. Six near-duplicate `gh api` ruleset permissions
There are six per-repo rules, `Bash(gh api -X PUT repos/acme/{api,web,cli,docs,infra,sdk}/rulesets/*)`. They look like leftovers from a one-time rollout of branch rulesets across repos. You have two options:
- **If that rollout is finished (my recommendation):** remove all six. They pre-approve writes to branch protection.
- **If you still do this regularly:** collapse them into one rule. The trade-off is that the single rule also covers any *new* `acme/*` repo.

```sh
# Option A: remove them all
jq '.permissions.allow |= map(select(test("^Bash\\(gh api -X PUT repos/acme/[a-z]+/rulesets/\\*\\)$") | not))' \
  "$CLAUDE_CONFIG_DIR/settings.json" > "$CLAUDE_CONFIG_DIR/settings.json.tmp" \
  && mv "$CLAUDE_CONFIG_DIR/settings.json.tmp" "$CLAUDE_CONFIG_DIR/settings.json"

# Option B: collapse to one wildcard rule
jq '.permissions.allow |= (map(select(test("^Bash\\(gh api -X PUT repos/acme/[a-z]+/rulesets/\\*\\)$") | not)) + ["Bash(gh api -X PUT repos/acme/*/rulesets/*)"])' \
  "$CLAUDE_CONFIG_DIR/settings.json" > "$CLAUDE_CONFIG_DIR/settings.json.tmp" \
  && mv "$CLAUDE_CONFIG_DIR/settings.json.tmp" "$CLAUDE_CONFIG_DIR/settings.json"
```

### 6. Read permission for a directory that doesn't exist
`Read(<fixture>/nonexistent-dir/**)` points at a path that isn't on disk. It's dead.

```sh
jq '.permissions.allow |= map(select(startswith("Read(") and contains("/nonexistent-dir/") | not))' \
  "$CLAUDE_CONFIG_DIR/settings.json" > "$CLAUDE_CONFIG_DIR/settings.json.tmp" \
  && mv "$CLAUDE_CONFIG_DIR/settings.json.tmp" "$CLAUDE_CONFIG_DIR/settings.json"
```

Steps 1, 5 (option A) and 6 all run together leave `allow` as `["Bash(npm test)"]`. With option B instead, it is `["Bash(npm test)", "Bash(gh api -X PUT repos/acme/*/rulesets/*)"]`. I checked the jq filters against a copy of your file (output to stdout only). Check the result with `jq . "$CLAUDE_CONFIG_DIR/settings.json"`.

### 7. Transcripts from a deleted project
`projects/-gone-project/0a1b.jsonl` is a session whose `cwd` was `<fixture>/deleted-project`. That directory no longer exists, so nothing can resume or use this transcript. It's tiny (231 B), but it's clutter. If you might want the history, keep the backup copy rather than deleting it for good.

```sh
mv "$CLAUDE_CONFIG_DIR/projects/-gone-project" "$BAK/-gone-project"
```

---

## P3: disk clutter (low impact)

### 8. Orphaned plugin version `acme/widget@1.0.0`
`plugins/cache/acme/widget/1.0.0/.orphaned_at` = `1780000000000` (2026-05-28), which is about 4 months ago. It has been replaced by `1.1.0`. Claude Code normally clears orphaned versions after a grace period, so this one was missed. It's safe to remove. **Keep `1.1.0`.**

```sh
mv "$CLAUDE_CONFIG_DIR/plugins/cache/acme/widget/1.0.0" "$BAK/widget-1.0.0"
```

### 9. (Optional) Stale `.in_use` markers on `widget@1.1.0`
`1.1.0/.in_use/` has two markers, `999991` and `999992`. If those are process IDs, they can't belong to live processes: they are above the macOS PID limit (99998), and `ps` rejects them. They look like leftovers from sessions that crashed.

Only clear them when no Claude Code session is running:

```sh
ls "$CLAUDE_CONFIG_DIR/plugins/cache/acme/widget/1.1.0/.in_use"          # confirm first
mv "$CLAUDE_CONFIG_DIR/plugins/cache/acme/widget/1.1.0/.in_use" "$BAK/widget-1.1.0-in_use"
```

Also, there is no `plugins/installed_plugins.json` or `known_marketplaces.json` in this config dir. So I couldn't confirm from the registry that 1.1.0 is the installed version; I went by the orphan/in-use markers. If `acme/widget` isn't a plugin you use any more, uninstall it with `claude plugin uninstall widget@acme` instead of cleaning up by hand.

---

## Checked and fine (no action needed)
- **Git (`repo`)**: working tree is clean apart from the untracked `CLAUDE.md` (item 2). `dev` and `main` both sit at `b3446fb` and match `origin/dev` and `origin/main`. There are no stale or merged-but-undeleted branches, no stashes, no extra worktrees, and no remote-tracking refs that need pruning.
- **`Bash(npm test)`**: this repo has no `package.json`, but the rule is in *user*-level settings and is narrow and harmless. It probably serves your other projects. Keep it.
- **`.gitignore`**: it looks reasonable. The only open question is `CLAUDE.local.md`, if you pick that option in item 2.

## Undo
Everything above is moved into `$BAK` rather than deleted. To undo, move the files back. For example:

```sh
cp "$BAK/settings.json" "$CLAUDE_CONFIG_DIR/settings.json"
```

When you're satisfied, delete `$BAK`.
