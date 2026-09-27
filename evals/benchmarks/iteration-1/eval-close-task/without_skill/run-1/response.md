# DEMO-1 close-out: not closed, because one acceptance criterion fails

I did not mark DEMO-1 Done. The tests pass, but acceptance criterion 2, "slugify strips all punctuation", is not met. The docs are in sync, and the task stays **In Progress**.

## What I checked
- **Tests:** `test_basic` and `test_commas` pass. pytest isn't installed, so I ran them directly with python3.
- **AC1, "lowercases and joins words with hyphens":** met. `slugify('Hello World') == 'hello-world'`. **Checked.**
- **AC3, "unit tests pass":** met. **Checked.**
- **AC2, "strips all punctuation":** **not met, left unchecked.** `slug.py` only removes `,` and `.`:
  - `slugify('Hello, World!')` -> `'hello-world!'`
  - `slugify('C++ & Rust')` -> `'c++-&-rust'`
  - `slugify('a - b')` -> `'a---b'`
  - No test covers any other punctuation, which is why the tests pass anyway.

## What I changed (in the fixture repo, branch `feat/DEMO-1-slugify`)
- **Quest:** checked AC1 and AC3 on DEMO-1 as `claude` (delegated-agent, accountable human `jdn`). I also added an implementation note with the evidence and the AC2 failure. I did **not** run `quest task complete`, and I wrote no final summary, because the task isn't finished.
- **Lore:** ran `lore sync`. It regenerated `docs/log.md`, and a second run changed nothing. The story `docs/stories/slugify-helper.md` correctly stays `in-progress`, and its task table already matched the task. `lore check` reports 0 errors and 0 warnings, and `lore orphans` found nothing.
- **Git:** committed both files as `e3da481` ("DEMO-1: close-out review - AC1/AC3 verified, AC2 open; lore sync"). I pushed the feature branch to `origin`, which here is the local bare repo `fixture/remote.git`. There was no PR, as you said.
- **Not touched:** `dev` and `main` (nothing merged), and the code in `slug.py` / `test_slug.py`.

## What you need to decide (jdn)
1. **Fix the code, or narrow AC2.**
   - To fix it: strip every non-alphanumeric character, e.g. `re.sub(r'[^a-z0-9\s]', '', title.lower())`, then join the words with hyphens. Add tests for `!`, `?`, `:`, `&`, apostrophes and a stray ` - `.
   - To narrow it: if only commas and periods matter, rewrite AC2 to say so.
2. **Then close it:**
   - `quest task edit DEMO-1 --check-ac 2 --final-summary "..." ...`
   - `quest task complete DEMO-1 ...`
   - `lore sync`, which moves the story to done
   - commit, then merge through your usual flow
