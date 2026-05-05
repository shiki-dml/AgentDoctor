---
name: agent-eval-architect
description: Use this skill when designing or implementing generalized AI agent evaluation frameworks, agent capability schemas, eval packs, trace/result schemas, scoring rubrics, benchmark evidence registries, and pre-runtime outcome prediction reports. Do not use it for narrow fixture-specific bug patches.
---

# Agent Eval Architect Skill

## Purpose

Use this skill to design and implement generalized evaluation infrastructure for AI agents.

The goal is to build reusable, evidence-driven evaluation systems that can classify agent capabilities, select relevant eval packs, score experiment results, and generate cautious pre-runtime outcome predictions.

Do not use this skill for patching one specific output string or one specific fixture. Use it for framework-level design.

## Core Principles

1. Build generalized schemas before adding scenario-specific heuristics.
2. Separate agent identity from agent capability.
3. Do not judge an agent from its name alone.
4. Distinguish declared capability, observed behavior, experiment result, and prediction.
5. Base scores on evidence, traces, datasets, benchmark references, or explicit missing-evidence notes.
6. Never fabricate benchmark results.
7. Never imply that a benchmark applies to an agent unless the agent or comparable workflow was actually evaluated.
8. Prefer typed eval packs over a universal arbitrary-agent judge.
9. Support future specialized adapters without overfitting current samples.
10. Keep GitHub Pages static; experimental runs should be precomputed, local, CI-generated, or imported as data.

## Recommended Architecture

Implement a layered evaluation framework:

1. `AgentProfile`
   - What the agent claims it can do.
   - Tools, permissions, data access, autonomy level, execution environment, approval rules.
2. `CapabilityClassifier`
   - Map profile, tool, and task signals to one or more capability families.
   - Support multi-label classification.
3. `AgentTypeRegistry`
   - Define known agent families such as coding, file-reading, browser, contract-review, financial-simulation, research, and workflow automation.
4. `EvalPackRegistry`
   - Define reusable eval packs for each capability family.
   - Include tasks, expected evidence, scoring dimensions, risks, and required artifacts.
5. `ExperimentResult`
   - Store observed run results, traces, commands, artifacts, metrics, pass/fail labels, warnings, and failure modes.
6. `EvidenceResolver`
   - Connect an agent to historical runs, benchmark references, imported data, or missing-evidence warnings.
7. `ScoringEngine`
   - Compute weighted scores from observed results.
   - Report confidence and coverage, not just a single score.
8. `PredictionEngine`
   - Produce cautious pre-runtime outcome predictions.
   - Distinguish evidence-backed prediction from speculative estimate.
9. `ReportRenderer`
   - Produce Markdown and JSON reports explaining capabilities, evidence, limitations, risks, and recommended next evals.

## Required Capability Families

At minimum support these generalized types:

- `coding_agent`
- `file_reading_agent`
- `contract_review_agent`
- `browser_navigation_agent`
- `financial_transaction_agent_simulated`
- `research_agent`
- `workflow_automation_agent`
- `unknown_agent`

Financial transaction agents must be simulated-only unless the project later adds explicit sandbox and compliance controls. Do not implement real financial transactions.

## Generalization Requirements

Do not hard-code conclusions by exact agent name.

Correct examples:

- Agent has tools `["file_read", "file_write", "shell"]` and sample tasks involving repo patches, so classify it as `coding_agent` and `file_reading_agent`.
- Agent has browser navigation and form submission tools, so classify it as `browser_navigation_agent`.
- Agent has payment, transfer, or order execution tools, so classify it as `financial_transaction_agent_simulated` and `high_risk_action_agent`.

Incorrect examples:

- If name contains `Codex`, then classify it as `coding_agent`.
- If name contains `finance`, then classify it as a safe financial agent.
- If description contains "great at code", then assign a high score.

## Evidence Discipline

Classify the evidence source for every score:

- `observed_run`
- `imported_trace`
- `benchmark_reference`
- `simulated_eval`
- `manual_annotation`
- `declared_capability_only`
- `missing_evidence`

Declared capability alone must not create a high-confidence positive score.

## Benchmark And Research References

The system may include benchmark reference metadata for context, such as SWE-bench for coding agents or WebArena for browser agents.

Benchmark references are not direct scores unless the specific agent or workflow was evaluated under comparable conditions.

When web access is available and explicitly approved, prefer primary sources:

- Official benchmark websites
- Papers
- Official documentation
- Project repositories

If web access is unavailable, do not invent new claims. Add TODO references or use existing curated local reference metadata with clear provenance.

## GitHub Pages Constraint

GitHub Pages should display static and precomputed results only.

Do not build a runtime backend into GitHub Pages.
Do not make the browser run arbitrary agent experiments.
Do not run live financial or destructive actions from the browser.

## Testing Discipline

Add tests for:

1. Capability classification by tools and tasks, not exact names.
2. Multi-label agent classification.
3. Unknown agents receive eval plans, not fake confident scores.
4. Evidence-backed scoring differs from declared-only scoring.
5. Reports change when experiment results change.
6. Benchmark references do not become fake direct scores.
7. Financial transaction agents are simulation-only and high-risk by default.
8. README and project docs reflect implemented behavior.
9. Schemas are JSON-serializable.
10. No overfitting to sample agent names.

## Final Response Format

When completing an implementation, report:

1. Framework modules added.
2. Schemas added.
3. Eval packs added.
4. Scoring and prediction logic added.
5. Tests added.
6. README or `AGENTS.md` changes.
7. Commands run and results.
8. Remaining limitations and next specialized adapters.
