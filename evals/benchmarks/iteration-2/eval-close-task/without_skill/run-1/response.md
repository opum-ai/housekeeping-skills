# DEMO-1 close-out: stopped short of closing, because one acceptance criterion is not met

## Summary

The tests pass, but DEMO-1 is **not done** by its own acceptance criteria, so I did **not** mark it complete and did **not** merge it to `dev`. I recorded the evidence on the task, synced the docs, and pushed the feature branch. You need to decide how to handle AC2 (see "Your decision" below).

## What I verified

- `test_slug.test_basic` and `test_slug.test_commas` pass on `9a13a2c`. pytest isn't installed here, so I ran them through a plain `python3` import.
- AC2, "slugify strips all punctuation", **fails**. `slug.py` only removes `,` and `.`:
  - `slugify('Hello, World!')` -> `'hello-world!'`
  - `slugify('What? Yes: no; (maybe)')` -> `'what?-yes:-no;-(maybe)'`
  - `slugify('a/b & c')` -> `'a/b-&-c'`

  The tests only cover commas and periods, which is why they pass anyway.

## What I changed (all inside the fixture)

- **Quest** (actor `claude`, delegated-agent, accountable human `jdn`):
  - Checked AC1 (lowercase and hyphen-join) and AC3 (unit tests pass), each with evidence.
  - Left AC2 unchecked, and added a note on the task with the failing inputs above.
  - Status stays **In Progress**, and there's no final summary yet.
- **Lore:**
  - `lore sync` updated `docs/log.md`. The story's task table and its `in-progress` status already matched the tracker.
  - `lore check`: 0 errors, 0 warnings. `quest doctor`: healthy.
- **Git:**
  - Committed `c0f7fa6` ("DEMO-1: record verification evidence ...; lore sync") on `feat/DEMO-1-slugify`.
  - Pushed it to `origin` (the fixture's `remote.git`). The working tree is clean.
  - I skipped the PR as you asked. `dev` and `main` are untouched, locally and on origin, at `194045e`.

## Your decision on AC2

Pick one:
1. **Fix the code.** Strip all non-alphanumeric characters, and add a test that fails on the current code, such as `slugify('Hello, World!') == 'hello-world'`. Then check AC2 and close with `quest task edit DEMO-1 --final-summary ...` and `quest task complete DEMO-1`.
2. **Narrow AC2** to "strips commas and periods" if that was the real intent. Then check it and close.
3. **Close it anyway** with AC2 open. `quest task complete` allows this but records `unresolvedAtCompletion`. I didn't choose this for you.

After closing, run `lore sync` so the story moves to done, then merge to `dev` however you usually do (without a PR in this sandbox).

## Other things to know

- **`docs/log.md` never settles.** Every commit that touches `docs/log.md` makes the next `lore sync` add another entry for that commit. I stopped after one sync commit and threw away a second, unpushed one, so the tree is clean. Running `lore sync` again will show a one-line `docs/log.md` diff. This looks like a lore issue.
- **The story has empty sections.** In `docs/stories/slugify-helper.md`, "Goal", "Acceptance criteria" and "Notes" are empty. I left them for you rather than write content you didn't ask for.
- **Version mismatch in CLAUDE.md.** The fixture's managed block pins Quest 0.11.0, which matches the installed CLI. The outer repo's CLAUDE.md says 0.10.0, but that's outside this sandbox.
