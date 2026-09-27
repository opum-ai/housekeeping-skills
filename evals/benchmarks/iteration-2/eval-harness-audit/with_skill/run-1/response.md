# Claude Code setup audit: prioritized cleanup list

This was an audit only. I changed nothing you asked me to keep. The survey was the
harness-hygiene skill's read-only engine plans (`hk plan --level deep --domains harness`)
at repo and machine scope, run with your `CLAUDE_CONFIG_DIR`. I also read every flagged
file myself and ran `claude project purge --dry-run` and `claude plugin list`.

One side effect to report. Pointing the `claude` CLI at this config dir made it
initialize `.claude.json`: it added first-start fields, wrote a `backups/` copy, and left
a stray `.claude.json.tmp.*` file. I restored all three byte for byte. A `hk apply --dry-run`
also created an empty `.git/housekeeping/journal`, which I removed. Your config dir and
repo are as I found them.

Shorthand for the commands below (zsh-safe):

```bash
export CLAUDE_CONFIG_DIR=<workspace>/iteration-2/eval-harness-audit/with_skill/run-1/fixture/claude-home
FIX=<workspace>/iteration-2/eval-harness-audit/with_skill/run-1/fixture
REPO="$FIX/repo"
MEM="$CLAUDE_CONFIG_DIR/projects/-private-tmp-claude-501--Volumes-external-repos-housekeeping-skills-88482b1c-3570-4612-a5d0-34d34963c60a-scratchpad-hk-workspace-iteration-2-eval-harness-audit-with-skill-run-1-fixture-repo/memory"
PLAN=<workspace>/iteration-2/eval-harness-audit/with_skill/run-1/outputs/plan-machine.json
hk() { python3 <repo>/scripts/hk.py "$@"; }
```

## Summary

| # | What | Why it matters | Risk of the fix |
|---|---|---|---|
| 1 | 8 of 9 permission allow rules are stale, one-off, or too broad | Standing approval for **remote writes** and for **any `rm`** | Low. You can re-add a rule any time |
| 2 | Repo `CLAUDE.md` is 420 lines, and it is untracked | Loaded into every session (the guide is 300 or fewer) | Low. Content moves, it is not deleted |
| 3 | `MEMORY.md` has 190 lines that all point to files that don't exist, plus 1 superseded memory | 190 lines of dead context every session | Low |
| 4 | Transcripts for a project whose folder is gone (`fixture/deleted-project`) | Clutter only (4 KB) | **Irreversible** (S3) |
| 5 | Plugin cache: an orphaned `acme/widget@1.0.0`, plus 2 in-use markers left by dead processes on 1.1.0 | Markers can pin an outdated plugin version | Low (S2, reinstallable) |
| 6 | Checks that only you can run from inside a session | Covers what I can't see from outside | None |

---

## 1. Permissions: `$CLAUDE_CONFIG_DIR/settings.json` (highest priority)

Engine finding `har-83cd2543`: 8 of the 9 allow rules are a problem.

| Rule | Problem |
|---|---|
| `Bash(gh api -X PUT repos/acme/{api,web,cli,docs,infra,sdk}/rulesets/*)` (6 rules) | Standing approval for **writes to GitHub remote state**. The six differ only in the repo name, so they look like one ruleset rollout that has already happened. |
| `Bash(rm:*)` | Overly broad: it pre-approves any `rm`, including `rm -rf` anywhere. |
| `Read(.../fixture/nonexistent-dir/**)` | The path no longer exists. |
| `Bash(npm test)` | Fine. Keep it. |

**Proposed replacement:** keep only `Bash(npm test)`.

```bash
python3 - "$CLAUDE_CONFIG_DIR/settings.json" <<'EOF'
import json, sys
p = sys.argv[1]; s = json.load(open(p))
s["permissions"]["allow"] = ["Bash(npm test)"]
json.dump(s, open(p, "w"), indent=2)
EOF
```

You can also make the same change interactively with `/permissions` in a session.

- **If the rulesets rollout is still running:** use a single rule,
  `Bash(gh api -X PUT repos/acme/*/rulesets/*)`, instead of six. Remove it when the
  rollout is done. I'd still rather approve remote writes per use.
- **If you need `rm` pre-approved:** narrow it to what you actually run, for example
  `Bash(rm -rf dist)` or `Bash(rm -rf node_modules)`.

## 2. `$REPO/CLAUDE.md`: 420 lines, untracked (finding `har-baf30c6f`)

- **Size.** Every session loads all 420 lines. The file is one flat list,
  `- Rule 0` … `- Rule 419: always do thing N carefully`, with no headings and no
  managed blocks. The text doesn't tell me which rules are always needed and which are
  situational, so you need to mark them.
- **Untracked.** `git status` shows `?? CLAUDE.md`. It isn't committed, so collaborators
  and fresh clones don't get it. Decide which kind it is:
  - **Shared project instructions:** commit it after slimming.
  - **Personal:** rename it `CLAUDE.local.md` and gitignore it.

Proposed flow. Nothing is edited until you pick the rules.

```bash
cd "$REPO"
wc -l CLAUDE.md                                   # 420 now; target well under 300
# 1. You mark which rules are always-needed; those stay in CLAUDE.md.
# 2. Situational rules move to an on-demand skill (loaded only when relevant), e.g.:
mkdir -p .claude/skills/project-rules
#    write .claude/skills/project-rules/SKILL.md with a frontmatter description of
#    when the rules apply, then the moved rules; delete those lines from CLAUDE.md.
#    Rules about one subdirectory go in <subdir>/CLAUDE.md instead.
# 3. Show before/after line count and diff, then:
git add CLAUDE.md .claude/skills/project-rules/SKILL.md
git commit -m "Slim CLAUDE.md: move situational rules into a skill"
#    If it is personal instead: mv CLAUDE.md CLAUDE.local.md && echo CLAUDE.local.md >> .gitignore
```

Note that `@path` imports inside CLAUDE.md are still loaded every session, so they don't
save context. A skill or a nested CLAUDE.md does.

## 3. Auto-memory: `$MEM`

- **`MEMORY.md` is 190 lines** (finding `har-ec5539bf`; the guide is 150 or fewer). The
  engine only flagged the length. When I read it, all 190 entries (`[Note 0](note0.md) —
  fact 0` … `note189.md`) point to files that **do not exist**. The directory holds only
  `MEMORY.md` and `old-deploy.md`. The entries also carry no content ("fact N"). As it
  stands, the whole index is dead context.
- **`old-deploy.md`** (finding `har-175a5c44`) reads "Deploy with make ship.
  **SUPERSEDED** by the release workflow". It isn't listed in `MEMORY.md`, and no memory
  about the release workflow exists to fold it into.

My recommendations:
- **`MEMORY.md`:** empty the index. If the note files were lost rather than never
  written, restore them from backup first, and don't run this.
- **`old-deploy.md`:** delete it. Optionally, add a one-line memory that describes the
  release workflow.

```bash
ls "$MEM"                                              # confirm: MEMORY.md, old-deploy.md only
mv "$MEM/old-deploy.md" ~/.Trash/                      # recoverable delete
: > "$MEM/MEMORY.md"                                   # clear the 190 dangling entries
```

## 4. Transcripts of a deleted project (S3, irreversible)

Engine item `har-2c324956`. The folder `$FIX/deleted-project` is gone, but
`$CLAUDE_CONFIG_DIR/projects/…-fixture-deleted-project/` still holds one transcript,
`0a1b.jsonl`. It is a single line containing only a `cwd` record, so there is nothing
worth saving with `/export`.

I already ran the preview:
```bash
claude project purge "$FIX/deleted-project" --dry-run  # result: "1 item(s) would be deleted"
```
To do it, run either of these after you confirm by name:
```bash
claude project purge "$FIX/deleted-project" -y
# or through the engine (journaled):
hk --root "$REPO" apply "$PLAN" --only har-2c324956 --confirm har-2c324956
```
Old `.claude.json` backups may still mention the project. They rotate out by themselves
(at most 5 are kept).

## 5. Plugin cache (S2, one batch approval)

| Item | What | Size |
|---|---|---|
| `har-1f62c9c9` | `plugins/cache/acme/widget/1.0.0`. Claude Code marked it orphaned, and nothing ever deletes those. | 8 KB |
| `har-4178326b` | `plugins/cache/acme/widget/1.1.0/.in_use/999991` and `999992`. These are markers for processes that are no longer running, and they can pin an outdated version. | 0 B |

```bash
hk --root "$REPO" apply "$PLAN" --only har-1f62c9c9,har-4178326b --approve-s2
```
I dry-ran this command: both items would apply. **Keep `--only`**: the saved plan also
lists items outside this sandbox (see "Not recommended" below).

One question for you: `claude plugin list` reports **no plugins installed** in this
config dir, so `acme/widget@1.1.0` isn't referenced either. If you don't use it, remove
the whole cache entry. It is reinstallable from its marketplace.
```bash
rm -rf "$CLAUDE_CONFIG_DIR/plugins/cache/acme"
```

## 6. Checks for you to run in a session

These are slash commands, so I can't run them:
- **`/doctor`:** the full checkup (unused extensions, CLAUDE.md bloat, slow hooks,
  allowlist consolidation). It can apply fixes itself.
- **`/context`:** confirms how much items 2 and 3 cost per turn, before and after.
- **`/hooks`, `/mcp`, `/memory`:** double-check the areas I found clean.

## What looked clean

- **Hooks:** there are none in `settings.json`.
- **MCP servers:** `.claude.json` has no project entries and no servers.
- **Duplicate skills:** the repo has no `.claude/skills`.
- **Background agents and schedules:** I didn't check these. Run `claude agents` and
  `/schedule`.

## Not recommended (outside this sandbox)

The machine-scope plan also listed **51 `scratchpad.old` items (about 1.1 GB)**, for
example the 922 MB `…-opum-cli-e2e/f1a6d24c…` and the 139 MB `…-opum-agent/a713428b…`.
They are under the real `<tmp>`, not in your fixture: the engine finds
scratchpads from `/private/tmp/claude-<uid>` and ignores `CLAUDE_CONFIG_DIR`. I left them
out. Three of them aren't session scratchpads at all, so a future real run shouldn't
delete them without review:
- `<tmp>` (Claude Code's bundled-skills
  extraction);
- `lore070/node_modules`;
- `ofle/.quest`.

The current session's scratchpad was correctly protected.

Saved plans (read-only artifacts):
- `outputs/plan-repo.json`
- `outputs/plan-machine.json`
