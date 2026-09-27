# Runtime cleanup: fixture/repo

Skill used: **runtime-clean**, run as `hk plan --level standard --domains runtime` at the default repo scope. I didn't use machine scope because you asked for this repo only.

## What I stopped

| pid | what | port | evidence |
|---|---|---|---|
| 64522 | `python3 -m http.server 0 --bind 127.0.0.1 --directory …/fixture/repo` | 127.0.0.1:59730 | Its working directory is inside `fixture/repo`. Its parent was an `sh -c … nohup …` shim (pid 64521) that had been reparented to init, so it's orphaned (`process.orphan`, S2). |

- It was stopped with SIGTERM through `hk apply --only run-ef686fd2 --approve-s2`. Your request to stop whatever this repo left running counts as the approval for this one S2 item, since it's clearly tied to this repo.
- The `sh` shim (pid 64521) exited along with it. Nothing else needed killing and I didn't need SIGKILL.
- **Verified:** nothing is listening on port 59730 any more. A fresh runtime plan for the repo shows 0 items and 0 findings.
- **Space reclaimed:** 0 B, since this only stopped a process.
- **Undo:** run `hk undo …/fixture/repo/.git/housekeeping/journal/20260927T091657-standard.jsonl`, or restart the server with the same `python3 -m http.server` command.

## What I left alone, and why

- **pid 64525, with its `sh` shim pid 64524:** another `python3 -m http.server`, listening on 127.0.0.1:59731.
  - Its working directory is `fixture/someone-elses-project`, which is outside this repo, so it isn't this repo's to stop.
  - I didn't touch it. If you want it stopped too, it's `kill 64525`, but check whose it is first.
- **Docker:** I didn't touch it. `hk` only looked at the active context (`orbstack`), and there was nothing for this repo in the plan.
- **Files:** none were changed. The repo's working tree is clean.
