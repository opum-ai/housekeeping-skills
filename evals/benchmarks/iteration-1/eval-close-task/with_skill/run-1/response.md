# DEMO-1 close-out report

**Level: C3 Clean.** The task is finished and you asked me to close it out. I skipped the PR and merge steps as you instructed, since there is no GitHub remote. I acted as `claude` (delegated-agent) on behalf of `jdn`.

## Heads-up: one acceptance criterion is not met

AC2, "slugify strips all punctuation", is false. `slug.py` removes only `,` and `.`, and the tests only cover those two characters. Probes:
- `slugify("Hello, World!")` returns `"hello-world!"`
- `slugify("What? (v2): yes;")` returns `"what?-(v2):-yes;"`

I did **not** change the code, because you said the work was done. Instead:
- I closed DEMO-1 with AC2 left unchecked. Quest recorded this as `unresolvedAtCompletion`.
- I filed **DEMO-2 "Make slugify strip all punctuation"** (To Do) to carry AC2, with verifiable criteria, and linked it to the story.

If you would rather have the fix in DEMO-1 itself, run `quest task demote DEMO-1 --to "In Progress"`, fix `slug.py` and add a test, then complete it again. After that, archive DEMO-2.

## Recorded (tracker and docs)

**DEMO-1:**
- AC1 and AC3 checked, based on evidence: `test_basic` and `test_commas` pass at 901badc, exit 0. I ran them directly with python3 because pytest is not installed here.
- Evidence note added, plus a follow-up pointer to DEMO-2, and modified files recorded.
- Completed with `quest task complete` and a final summary. The summary covers what changed, why, how it was verified, the AC2 gap, and that no PR was opened.

**DEMO-2:** created. Nothing matched in `quest search` first. Linked to `stories/slugify-helper` with `lore link`.

**Story `docs/stories/slugify-helper.md`:**
- The empty Goal and Acceptance-criteria sections are filled in from the task.
- A "Deviations" note under Notes names DEMO-2.
- `lore sync` regenerated the task block (DEMO-1 Done, DEMO-2 To Do), set `lore_task_status: todo`, and updated `docs/log.md`.

**Gates:** all passed.
- `lore check`: 0 errors
- `lore validate`: 0 errors
- `quest agents --check --require-installed --target claude`: current
- `lore agents --check`: up to date
- `quest doctor`: healthy
- `lore orphans`: none

## Landed

- One commit on `feat/DEMO-1-slugify`: **97a985a** "DEMO-1: close task, file DEMO-2 for unmet AC2, sync story". It contains the `.quest/` move of DEMO-1 to `completed/`, the new DEMO-2, the story, and `docs/log.md`.
- Before committing, I scanned the staged changes for secrets (gitleaks is not installed, so I used a pattern grep). Nothing was found.
- Pushed to origin (the local bare remote). The branch is ahead 0 / behind 0 and the working tree is clean.
- **Not merged into `dev`** because the PR step was skipped. The branch has 4 commits that are not in `origin/dev`.

## Cleared

Nothing. After landing, `hk plan --level C3` planned 0 items. Its only findings were the task branch itself (unlanded; protected because it is checked out) and its remote copy (unlanded). Both are expected until you merge. hk also noted that gh could not prove PR state, because there is no GitHub remote. So there is no journal and no bytes reclaimed.

## Skipped, or left for you

1. **Merging.** You need to merge `feat/DEMO-1-slugify` into `dev` using your usual process. After the merge, delete the local branch; `hk plan --level C3` will then show it as landed.
2. **AC2 / DEMO-2.** Decide whether to fix it under DEMO-2 (as filed) or reopen DEMO-1.
3. **`docs/log.md` lags one commit.** It is generated from commits that touch `docs/`, so it can never include the commit that contains it. I discarded the regenerated one-line entry for 97a985a so the tree stays clean. The next `lore sync` adds it back, and `lore check` passes either way.
4. **pytest is not installed** in this environment. The tests were run by calling the test functions directly.

Nothing outside the fixture directory was modified.
