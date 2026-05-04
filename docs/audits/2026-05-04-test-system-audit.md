# Test System Audit - 2026-05-04

## Scope

This audit covered the Contract2Agent Python package, pytest suite, CLI smoke
coverage, report rendering, README/docs integrity, GitHub Pages static demo,
static assets, and CI configuration.

Inspected areas included:

- `README.md`
- `pyproject.toml`
- `.gitignore`
- `.github/workflows/`
- `contract2agent/cli.py`
- `contract2agent/checker.py`
- `contract2agent/diagnosis.py`
- `contract2agent/diagnosis_schema.py`
- `contract2agent/schema.py`
- `tests/`
- `docs/index.html`
- `docs/assets/app.js`
- `docs/assets/styles.css`
- `docs/assets/contract2agent-preview.svg`
- `docs/examples/`
- `docs/audits/`

## Existing Features Found

- `pyproject.toml` already uses PEP 621 metadata and declares `pytest>=7.0`
  under `[project.optional-dependencies].dev`.
- The `c2a` console script already points to `contract2agent.cli:main`.
- A legacy `agentdoctor` console-script alias exists for backwards
  compatibility; this audit did not remove it because that would be a public
  packaging behavior change outside the requested test/evaluation integration.
- The Python suite already covered parser behavior, checker behavior,
  diagnosis categories, strictness, affected agent parts, rule coverage,
  patch suggestions, regression trace generation, CLI smoke paths, baseline
  snapshots, diagnostic modes, cost estimates, patch preview, triage, and
  existing GitHub Pages static checks.
- Markdown diagnosis report rendering already existed through
  `write_diagnosis_report_markdown`.
- YAML diagnosis report rendering already existed through
  `write_diagnosis_report_yaml`.
- `docs/index.html`, `docs/assets/app.js`, `docs/assets/styles.css`,
  `docs/assets/contract2agent-preview.svg`, and static sample cases under
  `docs/examples/` already existed.
- `docs/audits/2026-05-04-bug-audit.md` already existed and was preserved.
- `.github/workflows/docs.yml` already existed for MkDocs Pages deployment.

## Preserved

- No core Python source behavior was changed.
- Existing diagnosis schema objects, checker behavior, parser behavior, CLI
  commands, report writers, rule coverage logic, and regression trace helpers
  were preserved.
- Existing tests were kept and strengthened additively.
- Existing static demo inputs, sample buttons, diagnosis output, Markdown copy,
  JSON copy, sample loading, and reset behavior were preserved.
- `docs/`, `docs/audits/`, and existing docs pages were preserved.
- Generated output, caches, local virtual environments, runtime `.agentdoctor`
  data, and ignored report directories were not committed.

## Changes Made

### GitHub Pages Evaluation Lab

Changed files:

- `docs/index.html`
- `docs/assets/app.js`
- `docs/assets/styles.css`

What changed:

- Added a visible `Evaluation Lab` section next to the diagnosis result.
- Added static quality metrics for Input Completeness, Evidence Coverage,
  Detected Issues, Clause Signals, Risk Signal, and Markdown/JSON export
  readiness.
- Added a deterministic Generated Test Case Preview.
- Added a `Copy Test Case JSON` action alongside existing Markdown/JSON copy
  actions.
- Added text explaining that the browser preview mirrors the repository's
  testing philosophy and does not run pytest in the browser.

Why necessary:

- The existing Pages demo had useful structured diagnosis output, but it did
  not expose the requested evaluation/testing layer to users.

Alternatives considered:

- A backend or browser pytest runner was rejected because the project is
  static-first and the requirement explicitly disallows backend services,
  API keys, heavy frontend frameworks, and misleading claims that pytest runs
  in the browser.
- A new frontend framework was rejected because the existing vanilla HTML/CSS/JS
  page was working and could be extended cleanly.

Tests protecting the change:

- `tests/test_docs_site.py` now verifies the Evaluation Lab labels, generated
  test-case preview, copy button wiring, static no-network behavior, deployable
  relative assets, and optional `node --check` syntax validation.

### Golden Fixtures

Changed files:

- `tests/fixtures/golden/missing_file_expected.json`
- `tests/fixtures/golden/forbidden_tool_expected.json`
- `tests/fixtures/golden/valid_trace_rejected_expected.json`
- `tests/fixtures/golden/service_payment_expected.json`
- `tests/test_golden_diagnosis.py`

What changed:

- Added compact golden fixtures that lock stable diagnosis fields without
  snapshotting entire Markdown reports.
- Covered missing-file write-after-error, forbidden tool checker miss, valid
  trace rejected as too strict, and the service payment static sample.

Why necessary:

- The suite already had many deterministic diagnosis tests, but no checked-in
  golden fixture directory.

Tests protecting the change:

- `tests/test_golden_diagnosis.py` compares issue IDs, categories,
  strictness, affected agent parts, cause substrings, suggested patch types,
  regression trace tools, and service payment sample fields.

### Report Rendering Coverage

Changed files:

- `tests/test_report_rendering.py`

What changed:

- Added focused tests for required Markdown report sections and artifact-free
  rendering.
- Added a JSON-serialization test for `DiagnosisReport.to_dict()` to protect
  structured fields, suggested patches, regression traces, and rule coverage.

Why necessary:

- Existing report tests checked key Markdown fields, but the requested
  evaluation system called for explicit protection against visible `None`
  placeholders, Python reprs, object memory addresses, and non-serializable
  structured fields.

Tests protecting the change:

- `tests/test_report_rendering.py`.

### Schema Defaults

Changed files:

- `tests/test_diagnosis_schema.py`

What changed:

- Added a schema test proving default evidence, confidence reasons,
  responsibility, enum string values, suggested patch, and regression trace
  fields remain JSON-serializable.

Why necessary:

- Existing schema tests covered required fields and confidence bounds but did
  not directly assert the default container fields.

### Static Site Tests

Changed files:

- `tests/test_docs_site.py`

What changed:

- Strengthened static site tests to verify deployable relative CSS/JS/image
  assets, no local-only paths, no required backend calls, no hardcoded API
  calls, Evaluation Lab content, generated test-case preview content, and copy
  action wiring.
- Added optional `node --check docs/assets/app.js` execution when Node.js is
  available, with static fallback assertions when it is not.

Why necessary:

- The existing static tests checked important basics but did not fully verify
  the critical GitHub Pages runtime requirements.

### README

Changed files:

- `README.md`

What changed:

- Replaced legacy hardcoded demo URLs with `docs/index.html` and generic
  GitHub Pages deployment instructions.
- Added Evaluation-first design, Evaluation Lab, Golden tests, CLI smoke tests,
  GitHub Pages static tests, and GitHub Pages readiness checklist sections.
- Documented how the web demo maps to pytest, golden fixtures, CLI reports, and
  regression cases.
- Kept the not-legal-advice disclaimer.

Why necessary:

- The README needed to explain the testing/evaluation system and avoid
  presenting the project as a legacy-named product.

Tests protecting the change:

- `tests/test_docs_site.py` checks README identity, local links, internal
  anchors, evaluation-first content, and disclaimer language.

### CI

Changed files:

- `.github/workflows/ci.yml`

What changed:

- Added a general CI workflow that installs `.[dev]`, runs `python -m pytest`,
  optionally checks JavaScript syntax if Node is available, and runs
  `git diff --check`.

Why necessary:

- A docs deployment workflow existed, but there was no general pytest CI
  workflow.

## Dependency Changes

- No dependency changes were needed. `pytest>=7.0` was already present in the
  `dev` optional extra.
- No LLM API dependency, backend service, npm build step, browser automation
  framework, or heavy frontend framework was added.

## Commands Run

- `git status --short`
- `git diff --check`
- `rg --files`
- `git remote -v`
- `python -m pytest`
- `node --version`
- `node --check docs\assets\app.js`
- `python -m pytest tests\test_docs_site.py tests\test_golden_diagnosis.py tests\test_report_rendering.py tests\test_diagnosis_schema.py`

## Verification Results

- Baseline before edits: `python -m pytest` collected 215 tests and passed.
- Focused verification after edits: 47 selected tests passed.
- Full verification after edits: `python -m pytest` collected 225 tests and
  passed.
- `git diff --check` passed.
- `node --check docs\assets\app.js` passed.

## GitHub Pages Readiness

- `docs/index.html` exists directly under `docs/`.
- `docs/index.html` references `assets/styles.css`, `assets/app.js`, and
  `assets/contract2agent-preview.svg` with relative paths.
- All referenced local CSS/JS/image assets exist.
- The page does not require a dev server, backend, API keys, LLM API, npm
  install, or build step.
- Static tests check that `docs/index.html` does not reference `localhost`,
  `127.0.0.1`, `C:\`, `/mnt/`, or `/Users/`.
- `docs/assets/app.js` uses deterministic browser-side logic and no network
  calls.

## Remaining Limitations

- The Python package's core diagnosis system currently focuses on agent
  contract/trace diagnostics. The public GitHub Pages page presents a
  deterministic contract-dispute diagnosis preview. The Evaluation Lab bridges
  these product surfaces through structured inputs, expected outputs, golden
  case previews, and report/export readiness, but the browser does not execute
  the Python diagnosis engine.
- JSON report file output is not a current CLI format for diagnosis reports;
  the suite protects JSON-serializable report data through
  `DiagnosisReport.to_dict()` instead of inventing a new CLI output mode.
- The existing `.github/workflows/docs.yml` deploys MkDocs output. The new CI
  workflow is separate and focused on tests/static checks. Repository owners
  should choose whether Pages is published by the existing workflow or by
  configuring GitHub Pages to serve `/docs` directly.
