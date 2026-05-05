---
name: research-grounded-eval
description: Use this skill when collecting, importing, or citing benchmark, paper, documentation, or experiment evidence for agent evaluation frameworks. It prevents fabricated benchmark claims and keeps external research as contextual evidence rather than direct scores.
---

# Research Grounded Eval Skill

## Purpose

Use this skill when agent evaluation work needs external benchmark references, research papers, public datasets, official docs, or imported experiment results.

The goal is to make the evaluation framework more general and evidence-aware without hallucinating benchmark claims.

## Rules

1. Prefer primary sources:
   - Official benchmark websites
   - Official benchmark repositories
   - Papers
   - Official API and documentation pages
   - Project-owned experiment result files
2. Do not cite blogs, Reddit, leaderboards, or third-party summaries as primary evidence unless no primary source exists.
3. Do not scrape or import large external datasets unless explicitly requested.
4. Do not add network dependencies to the production package.
5. Do not make GitHub Pages call external APIs at runtime.
6. Do not claim that an agent achieved a benchmark score unless:
   - The agent was actually evaluated.
   - The environment is documented.
   - The task set is documented.
   - The result source is stored or cited.
7. Distinguish:
   - `benchmark_reference`
   - `comparable_method`
   - `imported_experiment_result`
   - `observed_project_run`
   - `declared_capability`
   - `missing_evidence`
8. Use external research to improve the evaluation taxonomy, scoring dimensions, and task design.
   Do not turn it into a fake score.

## Recommended References To Look For

For coding agents:

- SWE-bench
- SWE-bench Verified
- Issue-to-patch benchmarks
- Unit-test-based evaluation methods

For browser and navigation agents:

- WebArena
- VisualWebArena
- BrowserGym
- Task-state programmatic evaluation methods

For trace and eval methodology:

- OpenAI agent evals
- Trace grading
- Datasets and eval runs
- Grader design

For financial and action agents:

- Simulated transaction safety
- Authorization and approval workflows
- Auditability
- Refusal when unsafe
- Sandbox-only evaluation

## Data Model Guidance

When adding benchmark references, store them as structured metadata:

- `id`
- `title`
- `source_url`
- `source_type`
- `domain`
- `evaluated_capability`
- `evaluation_method`
- `task_count`, if known
- `primary_metric`
- `notes`
- `limitations`
- `citation`

Do not store unsupported claims.

## Final Response Requirements

Report:

1. Sources consulted.
2. Which sources were used as framework references.
3. Which claims were avoided because evidence was insufficient.
4. Files changed.
5. Tests added.
