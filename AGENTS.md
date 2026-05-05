# AGENTS.md

## Project

Contract2Agent is an evaluation-first framework for pre-runtime AI agent diagnosis, capability classification, eval category selection, evidence-backed preliminary scoring, and cautious outcome prediction.

The project is evolving from a narrow contract-dispute playground into a generalized agent evaluation framework that supports concrete agent categories through typed adapters and eval packs.

Core product flow:

AgentInput
-> AgentProfile normalization
-> capability signal extraction
-> capability classification
-> evidence source resolution
-> eval category selection
-> preliminary scoring
-> cautious pre-runtime outcome prediction
-> Markdown / JSON report generation

## Product Principles

- Do not build a fake universal judge for arbitrary agents.
- Build a generalized evaluation framework that supports many agent types through typed adapters and eval packs.
- Scores must be evidence-backed.
- Declared capabilities are not proof of performance.
- Missing evidence must be represented explicitly.
- Benchmark references are contextual evidence, not direct scores unless this project actually ran the comparable evaluation.
- Specialized agent families may be added later, but the framework must not overfit to exact sample names or fixtures.
- GitHub Pages must remain static unless a future task explicitly designs a safe non-static architecture.

## Current Priority

Prioritize Python core framework, schemas, deterministic scoring, eval packs, experiment result models, report rendering, README repositioning, and tests.

Do not prioritize GitHub Pages UI expansion until the core evaluation framework is stable.

## File Reading Agent Evaluation Priority

The first specialized agent adapter should be `file_reading_agent`.

This adapter must go beyond profile-only classification. It should support a CLI-based local evaluation runner that can import corpora, build or load tasks, run a target agent, capture traces, grade outputs, compare against reference results, and produce actionable improvement reports.

For file-reading agents, performance scores require observed runs. A profile-only assessment may produce readiness, risk, and recommended eval plans, but must not claim actual reading performance.

The file-reading evaluation framework should distinguish:

- declared file-reading capability
- tool-surface inference
- observed file-reading behavior
- answer correctness
- citation grounding
- file selection quality
- abstention behavior
- forbidden-file safety
- reference benchmark context
- comparable reference-agent results
- missing evidence

Reference benchmarks, public papers, and curated datasets may be used to design tasks or provide contextual comparison, but they are not direct scores unless the same agent or comparable workflow was actually evaluated under documented conditions.

Network import of public datasets or papers must be explicit and controlled. Prefer local import first. Any network-enabled import command must require an explicit `--allow-network` flag and must store source, license, provenance, and limitations metadata.

GitHub Pages must remain a static viewer/demo. Long-running file-reading evaluations should run in the CLI, local scripts, or CI-generated artifacts, not in the browser.

File-reading agent evaluation must include tests for:

- corpus manifest creation
- local file import
- task loading
- citation span verification
- answer grading
- unanswerable/abstention behavior
- forbidden-file boundary
- reference-result compatibility
- dummy-agent CLI runs
- report generation
- no observed score without observed run

## Supported Agent Families

The default framework should support:

- `coding_agent`
- `file_reading_agent`
- `contract_review_agent`
- `browser_navigation_agent`
- `research_agent`
- `workflow_automation_agent`
- `financial_transaction_agent_simulated`
- `unknown_agent`

Financial transaction evaluation is simulation-only. Do not implement real payment, trading, ordering, or other financial side effects.

## Preferred Skills

Use `agent-eval-architect` for framework-level evaluation architecture.
Use `file-reading-eval-architect` for file-reading corpora, tasks, runners, graders, comparisons, and reports.
Use `research-grounded-eval` when collecting or structuring benchmark and research references.
Use `smart-patcher` only for localized bug fixes and regression repairs.

## Setup

Use the repository's Python environment. If dependencies are missing, prefer the project's configured optional extras.

Common commands:

    python -m pip install -e ".[dev]"
    python -m pip install -e ".[docs]"
    python -m pytest
    python -m compileall -q contract2agent tests scripts
    python scripts/check_docs_links.py
    python -m mkdocs build --strict

## Implementation Rules

- Preserve deterministic behavior.
- Prefer dataclasses or existing project schema style unless Pydantic is already clearly required.
- Keep schemas JSON-serializable.
- Do not add production dependencies unless explicitly approved.
- Do not implement a runtime backend for GitHub Pages.
- Do not make the browser run arbitrary agent experiments.
- Do not implement real financial transactions.
- Financial transaction evaluation must remain simulated-only unless a future sandbox and compliance design is explicitly added.
- Do not hard-code exact sample agent names.
- Do not hard-code benchmark claims.
- Do not fabricate experiment results.
- Distinguish declared capability from inferred capability, observed evidence, reference evidence, prediction, and missing evidence.
- Keep README, CLI, docs, and tests aligned with implemented behavior.
- Preserve old contract diagnosis functionality unless intentionally deprecated and tested.

## Testing Rules

After framework changes, run:

    python -m pytest

When relevant, also run:

    python -m compileall -q contract2agent tests scripts
    python scripts/check_docs_links.py
    python -m mkdocs build --strict

Add focused tests for:

- schema serialization
- capability classification
- eval pack selection
- evidence-aware scoring
- unknown-agent handling
- benchmark-reference handling
- report generation
- README/docs integrity
- anti-overfitting behavior

## Cleanup Rules

- Do not commit caches, virtual environments, generated reports, local runtime data, or `.pyc` files.
- Keep intentional sample data under `examples/`, `tests/fixtures/`, or `docs/data/`.
- Sanitize local absolute paths before committing troubleshooting notes.

## Safety Rules

- Do not weaken path containment, secret filtering, generated-artifact exclusions, or command safety checks.
- Do not read or commit `.env`, credentials, tokens, SSH keys, browser data, or private user files.
- Do not remove regression tests added for bug fixes.
