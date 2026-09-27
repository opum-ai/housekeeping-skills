# Housekeeping report template

Use this shape for the final message of every pass. Fill in what happened and leave out
empty sections. Keep it scannable: the user reads it to decide whether anything still
needs them.

```markdown
## Housekeeping: C3 Clean (chosen because: PR #42 for HS-4 merged)

**Recorded**
- HS-4: progress note; criteria 1-3 checked (evidence: CI run 123456, `pytest` 48 passed); completed with a final summary citing PR #42 and run 123456
- lore sync rewrote docs/stories/tidy.md (task rollup); lore check exit 0

**Landed**
- 3 commits on feat/HS-4-tidy-skill, pushed; PR #42 squash-merged into dev
- local branch feat/HS-4-tidy-skill deleted after the merge (landed: PR #42 MERGED)

**Cleared** (journal: .git/housekeeping/journal/20260926T231500-C3.jsonl; `hk undo <journal>` reverses the S1 items)
| class | items | reclaimed | notes |
|---|---|---|---|
| S1 | 5 | 12 KB | 3 landed branches, 1 prunable worktree, 1 ignored junk log |
| S2 | 2 | 1.4 GB | approved as a batch: 1 stopped container, 1 orphaned dev server |
| S3 | 0 | - | none confirmed |

**Skipped**
- `git-3f2a…` feat/old-spike: branch moved since planning (drift), left alone

**Needs you** (outside this pass's reach, or protected)
- feat/experiment has 4 unlanded commits, idle 41 days: land it, or confirm archiving at C4
- ~/repos/lore-cli has 7 extra worktrees (another repo: its own session should clean them)

**Verify**: tree clean, ahead 0, no landed branches left, gates green.
```

## Clean-room certificate (C5 only)

Append this to the report and to the task's final summary or notes:

```markdown
### Clean-room certificate (2026-09-26T23:40, commit abc1234)
Rebuild from scratch:
| command | exit |
|---|---|
| npm ci | 0 |
| npm run build | 0 |
| npm test | 0 |

Remaining inventory (each item has a reason):
- .env: keep-list (local secrets, never removed)
- opum-runner container: protected (self-hosted CI runner)
- branch retain/2026-perf: reserved prefix, reason recorded in docs/...
```

State facts only. An absent signal is not a passing one. "No checks configured" and
"gh unavailable, PR proof skipped" belong in the report as written.
