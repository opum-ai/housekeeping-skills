# Generic branch flow (when opum-sdlc is not installed)

Use the repo's own rules first: `CONTRIBUTING.md`, the PR template, branch protection
(`gh api repos/<owner>/<repo>/rules/branches/<branch>`), and the conventions visible in
`git log`. This page fills the gaps.

## Detect the shape

| Signal | Shape | Trunk | Release |
|---|---|---|---|
| `origin/dev` (or `develop`) exists | two-branch (integration + release) | `dev` | `main` / `master` |
| only `origin/HEAD` → `main` | trunk-based | `main` | tags or none |
| `release/*` branches | release branches | `main` | `release/*` |

`hk status` reports the trunk and release it detected. `.housekeeping.toml` `[sdlc]`
overrides the detection.

## The sequence

```text
branch off origin/<trunk> -> commit in logical units -> push -u -> PR into <trunk>
  -> checks green on the head SHA -> merge (the repo's strategy) -> delete the local branch
  -> fetch --prune
```

- **Branch name:** follow the repo's pattern (`feat/…`, `fix/…`, `<user>/…`). Otherwise
  use `<type>/<issue-or-task-id>-<slug>`.
- **Merge strategy:** match what the repo's merged PRs show
  (`gh pr list --state merged --limit 5 --json mergeCommit,title`). When unknown, default
  to squash. Rebase merges and squash merges both leave the branch tip outside trunk's
  ancestry, which is why pruning uses the squash-equivalence and PR-state proofs.
- **Promotion:** fast-forward only. Merging `main` back into `dev`, or merging with a
  merge commit on `main`, breaks the fast-forward relationship for good.

## Repository settings worth checking (report; change only with the user)

- `delete_branch_on_merge`: remote head branches disappear on merge.
- `fetch.prune=true` (global) or `remote.origin.prune=true`: stale remote-tracking refs go
  away on fetch.
- Branch protection on the release branch: required checks, no force pushes.

- **A ruleset protecting the trunk and release branches from deletion and non-fast-forward
  pushes.** Without it, `delete_branch_on_merge` deletes `dev` the first time a `dev`→`main`
  promotion PR is recorded as merged, because `dev` is that PR's head branch. This was
  observed on this plugin's own first release.

None of these deletes the **local** branch after a merge. That step is always manual.
