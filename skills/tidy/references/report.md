# Housekeeping report template

Use this shape for the final message of every pass. Fill in what happened and leave out
empty sections. Keep it scannable: the user reads it to decide whether anything still
needs them.

```markdown
## Housekeeping: Standard, repo scope (chosen because: PR #42 for HS-4 merged)

**Recorded**
- HS-4: progress note; criteria 1-3 checked (evidence: CI run 123456, `pytest` 48 passed); completed with a final summary citing PR #42 and run 123456
- lore sync rewrote docs/stories/tidy.md (task rollup); lore check exit 0

**Landed**
- 3 commits on feat/HS-4-tidy-skill, pushed; PR #42 squash-merged into dev
- local branch feat/HS-4-tidy-skill deleted after the merge (landed: PR #42 MERGED)

**Cleared** (journal: .git/housekeeping/journal/20260927T231500-standard.jsonl; `hk undo <journal>` reverses the S1 items)
| class | items | reclaimed | notes |
|---|---|---|---|
| S1 | 5 | 12 KB | 3 landed branches, 1 prunable worktree, 1 ignored junk log |
| S2 | 2 | 1.4 GB | approved as a batch: 1 stopped container, 1 orphaned dev server |
| S3 | 0 | - | none confirmed |

**Skipped**
- `git-3f2a…` feat/old-spike: branch moved since planning (drift), left alone

**Needs you** (outside this pass's reach, or protected)
- feat/experiment has 4 unlanded commits, idle 41 days: land it, or confirm archiving in a Deep pass
- ~/repos/lore-cli has 7 extra worktrees (another repo: its own session should clean them)
- global caches hold 13 GB (machine scope: ask for a machine-scope pass to include them)

**Verify**: tree clean, ahead 0, no landed branches left, gates green.
```

## Disposition record (Immaculate only)

Append this to the report, put a summary on the task (a note or `--append-final-summary`),
and put the full record in the PR body:

```markdown
### Disposition record (2026-09-27T23:40, commit abc1234, repo scope): 0 unaccounted of 23

| item | disposition |
|---|---|
| branch feat/HS-4-tidy-skill | landed: PR #42 merged; local branch deleted |
| branch retain/2026-perf | kept: reserved prefix; reason recorded in docs/reference/perf-baseline.md |
| branch feat/experiment (4 unlanded commits) | deferred: HS-19 decides whether to land or drop it |
| .env | kept: keep-list (local secrets) |
| .idea/ | accepted: local IDE config, ignored by git |
| node_modules/ (1.1 GB) | removed: regenerable (npm ci) |
| task HS-4 | landed: completed with a final summary citing PR #42, CI run 123456 |
| docs/stories/tidy-orchestrator-skill.md | kept: rollup synced; lore check exit 0 |

Final-state checks:
| command | exit |
|---|---|
| hk disposition --level immaculate --scope repo | 0 |
| npm ci && npm run build && npm test | 0 |
| lore check | 0 |
```

State facts only. An absent signal is not a passing one. "No checks configured" and
"gh unavailable, PR proof skipped" belong in the report as written.
