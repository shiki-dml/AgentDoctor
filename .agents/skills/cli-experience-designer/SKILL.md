---
name: cli-experience-designer
description: Use this skill when improving CLI usability, help systems, colorful terminal output, progress display, command grouping, interactive prompts, no-color/json modes, and documentation examples.
---

# CLI Experience Designer Skill

## Purpose

Use this skill to make command-line tools easier to discover, more readable, and more pleasant to use without sacrificing scriptability or tests.

## Rules

1. Do not make colorful output mandatory.
2. Always provide `--no-color` or plain fallback.
3. Always keep machine-readable `--json` output where useful.
4. Do not make tests depend on ANSI colors.
5. Help text should explain workflows, not just options.
6. Provide example commands.
7. Keep error messages actionable.
8. Avoid excessive animation or slow UI.
9. Do not add heavy dependencies unless approved.
10. Prefer optional Rich integration if already available; otherwise use lightweight ANSI/plain text.

## Required CLI UX Features

For an evaluation CLI, prefer:

- Command groups
- Workflow help
- Scoring help
- Examples help
- Progress summaries
- Score tables
- Warning panels
- Improvement recommendation lists
- Doctor command
- Dry-run modes
- Verbose and quiet modes
- JSON output mode

## Final Response Expectation

Report:

1. Help commands added.
2. Output UX improvements.
3. Plain/no-color/json modes.
4. Tests added.
5. Documentation updated.
