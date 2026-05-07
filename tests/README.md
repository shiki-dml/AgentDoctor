# tests

## Responsibility

This directory contains the pytest suite and golden fixtures for Contract2Agent.

## Functionality

- Regression coverage for legacy contract diagnosis behavior.
- Generalized agent evaluation schema, classification, evidence, scoring, and report tests.
- File-reading eval corpus/task/run/grade/report and optional judge safety tests.
- Static docs and GitHub Pages demo checks.
- Developer workflow helper tests for triage, cost estimate, patch preview, baselines, and failure taxonomy.

## Test Command And Status

- Canonical command: `python -m pytest`.
- Pytest config is in `pyproject.toml`: `testpaths = ["tests"]`,
  `pythonpath = ["."]`, and `addopts = "-p no:cacheprovider"`.
- This README review did not run tests. Do not claim a current pass without
  fresh command output.

## Important Files And Entry Points

- `conftest.py`: shared pytest configuration.
- `fixtures/golden/`: golden diagnosis fixture outputs.
- `test_agent_evaluation_framework.py`: generalized agent evaluation behavior.
- `test_file_reading_eval.py`, `test_file_reading_llm_judge.py`: file-reading eval behavior.
- `test_docs_site.py`: docs/static site/README checks.

## Public Behavior Contracts

- Tests should not depend on ANSI color.
- Tests should avoid network and real API calls by default.
- Generated artifacts belong in ignored temp/runtime directories.

## Related Docs

- `../docs/harness/QUALITY_GATES.md`
- `../docs/harness/EVAL_MATRIX.md`
- `../docs/CODEMAP.md`

## Agent Notes

Future agents may add focused tests for behavior they change. Do not remove
regression tests added for bug fixes or safety boundaries.
