---
name: runtime-clean
description: Stop and remove the runtime leftovers of agentic work - dev servers and background processes a session started, orphaned node/bun/python processes still holding ports, this project's Docker containers, images, networks and volumes, dangling images and build cache - scoped by evidence (compose project label, working directory, provenance ledger) and never touching the self-hosted CI runner or someone's live terminal. Use this skill whenever the user says a port is already in use, asks to stop the dev server or kill background processes, wonders what is still running, wants Docker cleaned up or pruned, says containers or images are eating disk, or asks to shut everything down at the end of a session.
---

# runtime-clean

Processes and containers are live state, so the question is always **whose is this?**
"It looks unused" is not an answer. A dev server with a live parent is probably running in
someone's terminal. A container with no compose label may belong to another project, or
it may be the CI runner. This skill acts only on things it can attribute, and reports the
rest.

Engine: `HK="python3 <dir>/../../scripts/hk.py"`, where `<dir>` is the
`Base directory for this skill` that the Skill tool printed.

## Your own background work first

Stop what **you** started in this session with the tools that started it:
- background shells and tasks via the task tools (`/tasks` lists them);
- monitors;
- scheduled wakeups;
- cron jobs you created (CronList, then CronDelete).

These are the cheapest and safest to stop: you know exactly what they are. Then look
outward.

## Survey

```bash
$HK plan --level C3 --domains runtime --chosen-by "…"
lsof -nP -iTCP -sTCP:LISTEN          # who holds which port (read-only)
docker context show                  # hk inspects the active context only; say which
```

| Kind | Evidence | Level | Class |
|---|---|---|---|
| `process.session` | the provenance ledger recorded the command | C2 | S1 (SIGTERM; the undo is to re-run the recorded command) |
| `process.orphan` | cwd inside this repo, and reparented to init (possibly through a shim or `npm → node` chain) | C3 | S2 |
| `process.live` | cwd inside this repo, with a live parent (a terminal, an editor) | finding | ask whose it is |
| `process.orphan-foreign` | orphaned dev process outside this repo | C5 | S3 |
| `container.running` | ledger, or the compose project matches this repo | C2 / C3 | S1 (stop; the undo is `docker start`) |
| `container.stopped` | ledger or this project; C5 for others | C3 / C5 | S2 (its writable layer is gone) |
| `image.unused` / `image.dangling` | not used by any container; project-named images at C4 | C4 / C5 | S2 |
| `network.project` | compose project label | C4 | S1 |
| `volume.project` / `volume.dangling` | compose label / no references | C4 / C5 | **S3**: volumes hold databases |
| `docker.build-cache` | reclaimable | C5 | S2 |

**Protected everywhere:**
- containers and images in `[protect]`, including the built-in `opum-runner` and
  `*opum-actions-runner*`;
- the label `housekeeping.protect=true`;
- Claude Code itself, editors, language servers, pm2, and Docker/OrbStack.

**Port questions** ("port 3000 is in use"):
1. `lsof -nP -iTCP:3000 -sTCP:LISTEN` gives the pid.
2. Find that pid in the plan. Its kind says whether you may act.
3. A `process.live` holder belongs to a person: tell them rather than killing it.

## Judgement

- **Compose projects.** Prefer `docker compose -p <project> down` (without `-v`) from the
  project directory: compose knows its own resources. `down -v` deletes named volumes, so
  it is S3: confirm by volume name, and say what data lives there.
- **Volumes.** Before asking, find out what a volume holds
  (`docker volume inspect <v>`: its labels and mountpoint; the image of the container that
  used it). "postgres data for project X" is a decision the user can make. A bare volume
  hash is not.
- **Other Docker contexts.** `hk` sees only the active context. If the user runs several
  (OrbStack and Docker Desktop, say), report which one you inspected. Don't switch
  contexts to prune without asking.
- **Processes that ignore SIGTERM.** `hk apply` does not escalate. Report the process; use
  `--force-kill` (SIGKILL) only after the user agrees.
- **tmux / screen sessions** left by agents: list them (`tmux ls`) and report. Only kill
  sessions the ledger or their names tie to this session.

## Applying

```bash
$HK apply <plan.json> [--approve-s2] [--confirm id1,id2] [--force-kill]
```
- **S1** runs without asking.
- **S2** needs one batch approval via AskUserQuestion: count, what they are, the space
  reclaimed.
- **S3** needs each item confirmed by name via AskUserQuestion with `multiSelect`, nothing
  preselected.

Report:
- what stopped;
- what was removed;
- the space reclaimed;
- what you left and why (someone's live server, the CI runner, an unidentified volume).
