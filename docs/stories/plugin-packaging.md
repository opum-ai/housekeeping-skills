---
# yaml-language-server: $schema=../../.lore/schemas/arc.schema.json
type: Arc
title: Plugin packaging
tags:
  - release
summary: "Ship the plugin: plugin.json, README, a .housekeeping.toml example and a marketplace entry, validated by claude plugin validate and lore check."
tasks:
  - hs-12
generated:
  by: lore/0.9.3
  at: 2026-09-27T03:24:32.699Z
lore_task_status: todo
---

# Plugin packaging

## Goal

Ship the plugin so it installs cleanly, documents itself, and is listed in the marketplace.

## Acceptance criteria

- `claude plugin validate .` exits 0
- The README states install, levels, safety classes and benchmark results
- An example `.housekeeping.toml` documents every key

## Tasks

<!-- lore:tasks:begin -->
| Task | Title | Status |
|---|---|---|
| [HS-12](../../.quest/tasks/HS-12.json) | Package the plugin: plugin.json, README, .housekeeping.toml example, marketplace entry | To Do |
<!-- lore:tasks:end -->

## Notes

Part of [Housekeeping for agentic engineering](../epics/housekeeping-for-agentic-engineering.md).

- Keys and defaults come from the spec's [Configuration](../specs/cleanliness-levels.md#configuration) section.
- The marketplace entry lands in the same change that publishes the plugin.
- Ship only what runs: skills, scripts and the manifest. The research measured another
  plugin at about 620 MB per version from shipping its whole repo; see
  [Upstream findings](../reference/upstream-findings.md).
