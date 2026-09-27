## Housekeeping: Standard, repo scope (chosen because you asked to close out DEMO-1 as finished)

**DEMO-1 is not closed.** One of its three acceptance criteria is not met, so I did not run `quest task complete`. The rest of the close-out is done, and the task needs one decision from you (see "Needs you").

**What I found**
- The tests pass: both tests in `test_slug.py` pass (2 passed). pytest is not installed here, so I ran the two test functions directly with `python3 -B`.
- AC2, "slugify strips all punctuation", is **not met**. `slug.py` removes only `,` and `.`:
  - `slugify('Hello, World!')` returns `'hello-world!'`
  - `slugify('What? Yes: no')` returns `'what?-yes:-no'`
- No test covers any other punctuation, which is why the suite passes while AC2 fails.

**Recorded** (actor `claude`, delegated-agent, accountable human `jdn`)
- DEMO-1, AC1 checked. Evidence: `test_basic` passes (`'Hello World'` becomes `'hello-world'`).
- DEMO-1, AC3 checked. Evidence: 2 of 2 tests pass.
- DEMO-1, AC2 left unchecked, with the counter-examples above in a task note.
- DEMO-1: a second note gives the decision, the options, and my recommendation, so the next session can pick it up. I also recorded `slug.py` and `test_slug.py` as modified files.
- DEMO-1 stays **In Progress**.
- Docs: I added a "Deviations" note under Notes in `docs/stories/slugify-helper.md`. It says that slugs are not yet URL-safe and that DEMO-1 AC2 covers the gap. I did not edit anything inside the managed blocks, and the story's task rollup still correctly shows In Progress.
- `lore sync` rewrote `docs/log.md` to add one generated entry.
- All gates passed:

| command | result |
|---|---|
| `lore sync` | exit 0 |
| `lore check` | exit 0, both before and after the commit (0 errors, 0 warnings) |
| `quest agents --check --require-installed --target claude` | exit 0, current |
| `lore agents --check` | exit 0, up to date |
| `quest doctor --json` | healthy: true, no issues |
| `lore orphans --json` | no orphan, pending or dangling links |

**Landed**
- Commit `d56767e` on `feat/DEMO-1-slugify` holds the tracker change, the story note and the `lore sync` output together. It is pushed to `origin` (the local bare repo in the fixture).
- The secret scan of the diff found nothing.
- No PR, as you asked, since there is no GitHub remote. I did not merge into `dev` because the task isn't finished and nothing has reviewed the change.

**Cleared**
- Nothing. The `hk` Standard plan found 0 items to remove, both before and after landing, so there is no journal.
- The engine saved its plans under `.git/housekeeping/plans/`, outside the working tree.

**Findings (for your information only)**
- `feat/DEMO-1-slugify` has 4 commits that are not in `dev`, locally and on `origin`. That is expected: it is the task branch waiting for DEMO-1 to finish. It is kept because it is checked out and not landed.
- The fixture's CLAUDE.md block pins Quest 0.11.0, and that matches the installed CLI.

**Needs you: how should AC2 be resolved?**
- **(a) Fix the code (recommended).** The story promises URL-safe slugs. Make `slugify` strip every character that is not a letter, digit or whitespace, add tests for `! ? : ; ' " ( ) /`, then check AC2 and complete DEMO-1.
- **(b) Amend AC2** to "strips commas and full stops", if that was the intended scope. Then complete DEMO-1 and remove the deviation note from the story.
- **(c) Complete DEMO-1 now** with AC2 unresolved, and move the gap to a new follow-up task.

Tell me which one and I'll finish the close-out: `quest task complete DEMO-1` with a final summary citing the commit and test evidence, then `lore sync` (the story rollup becomes done) and `lore check`, all committed together.

**Verify**
- The working tree is clean, and the branch is 0 ahead and 0 behind `origin/feat/DEMO-1-slugify`.
- The gates are green.
- `hk plan --level standard` plans no removals and no landed branches.
- DEMO-1 is In Progress because of the open AC2.
