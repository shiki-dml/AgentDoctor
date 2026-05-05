---
name: file-reading-eval-architect
description: Use this skill when designing or implementing file-reading agent evaluation adapters, CLI eval runners, corpus/task/reference importers, evidence-grounding graders, citation graders, reference-result comparisons, and actionable reading-agent improvement reports.
---

# File Reading Eval Architect Skill

## Purpose

Use this skill for framework-level work on evaluating agents whose main job is to read files, select evidence, answer questions, cite sources, and respect file-access boundaries.

This skill is not for a superficial profile-only classifier. It is for actual CLI-driven evaluation over file corpora, tasks, traces, graders, reference results, and reports.

## Product Goal

Build a robust file-reading agent evaluation subsystem that can:

1. Import local files and curated reference packs.
2. Build or load evidence-grounded tasks.
3. Run a target file-reading agent for a configurable time or task budget.
4. Capture trace and output artifacts.
5. Grade answer correctness, citation grounding, file selection, abstention, safety, robustness, and efficiency.
6. Compare results against trustworthy reference runs when comparable.
7. Produce actionable improvement recommendations.

## Core Principles

1. Do not judge a file-reading agent from description alone.
2. A profile-only analysis is readiness analysis, not performance evaluation.
3. Real performance scores require observed runs.
4. Declared file-reading ability is not evidence of correctness.
5. Citations must be machine-checkable whenever possible.
6. File access must be bounded by explicit corpus manifests.
7. Forbidden-file and path-escape tests are required.
8. Reference benchmarks are contextual unless the same task pack and scoring method were run.
9. Do not fabricate public benchmark or reference-agent results.
10. Prefer deterministic graders over subjective judges.
11. Optional LLM or rubric graders must be clearly labeled and disabled by default.
12. Keep all imported sources with provenance, license, and limitations metadata.

## Required Evaluation Dimensions

A file-reading agent evaluation should cover:

- File selection precision and recall
- Supporting evidence recall
- Citation span accuracy
- Citation quote match
- Answer exact match, F1, or semantic correctness
- Hallucination or unsupported claim rate
- Unanswerable abstention accuracy
- Multi-file reasoning
- Long-document robustness
- Distractor resistance
- Conflicting evidence handling
- Forbidden file boundary
- Path containment
- Trace completeness
- Schema compliance
- Latency or time budget
- Cost proxy, file-read count, or token proxy
- Confidence calibration

## Required Task Families

Support task families such as:

- `single_file_qa`
- `multi_file_qa`
- `quote_lookup`
- `citation_required_qa`
- `unanswerable_question`
- `conflicting_evidence`
- `version_comparison`
- `timeline_extraction`
- `table_or_key_value_lookup`
- `policy_lookup`
- `needle_in_file`
- `needle_in_corpus`
- `distractor_resistance`
- `forbidden_file_boundary`
- `summary_with_citations`

## Required CLI Behavior

The CLI should support a long-running local evaluation runner with:

- Configurable time budget
- Configurable task budget
- Deterministic seed
- Run directory
- Corpus manifest
- Task file
- Target agent profile
- Target agent command adapter
- Trace capture
- Grading
- Comparison
- Markdown and JSON report output

Do not make GitHub Pages run live experiments.

## Target Agent Adapter

Prefer a black-box JSON adapter.

Input JSON should include:

- `task_id`
- `question`
- `corpus_dir`
- `allowed_files`
- `forbidden_files`
- `instructions`
- `output_schema`

Expected output JSON should include:

- `answer`
- `citations`
- `confidence`
- `files_read`, if available
- `notes`, if available

## Reference Data Discipline

When importing public datasets or papers:

1. Require explicit user action.
2. Store source metadata.
3. Store license and provenance notes.
4. Do not fetch network sources by default.
5. Use `--allow-network` for network import.
6. Mark imported benchmark references separately from observed experiment results.
7. Do not treat public benchmark references as direct scores.

## Report Requirements

Reports must include:

1. Task summary.
2. Score table by dimension.
3. Evidence and citation quality.
4. File selection behavior.
5. Safety boundary behavior.
6. Robustness results.
7. Reference comparison, if comparable.
8. Failure modes.
9. Improvement recommendations.
10. Next eval plan.
11. Limitations.
12. Trace appendix or artifact links.

## Testing Requirements

Add tests for:

- Schema serialization
- Corpus manifest creation
- Task loading
- Synthetic task generation
- Target output validation
- Deterministic graders
- Citation span checking
- Forbidden file detection
- Reference comparison compatibility checks
- CLI dry run
- CLI profile-only mode
- CLI observed-run mode with a dummy agent
- Report generation
- No fake score without observed runs
- No network import without explicit flag

## Safety

Do not read secrets, `.env`, SSH keys, browser data, or files outside user-approved corpora.

Do not implement real external actions.

Do not weaken existing path containment or secret filtering.

## Optional LLM judge layer

The file-reading eval subsystem may support optional LLM-based judging, but deterministic grading must remain the default.

LLM judges are allowed only when the user explicitly enables them.

Rules:

1. Never require LLM API calls for baseline grading.
2. Never call an API from GitHub Pages.
3. Never expose API keys in browser code, reports, logs, or committed files.
4. Prefer environment variables for API keys.
5. If an API key is entered interactively, use hidden input and keep it in memory for the current process only.
6. Mark all LLM-based scores as judge_based and non_deterministic.
7. Record provider, model, prompt version, token usage, and limitations when available.
8. Do not send entire corpora to the judge.
9. Send only task question, agent answer, cited snippets, gold answer/evidence when available, and minimal metadata.
10. Use deterministic graders first and send only uncertain/open-ended/failed tasks to the LLM judge unless the user explicitly requests all tasks.
11. Support budget controls such as max judge tasks, max input chars, max output tokens, cost budget, and cache.
12. Use structured JSON output for judge responses when possible.
13. LLM-generated recommendations must be grounded in measured failure modes.

## CLI UX requirements

The file-reading CLI should be usable as a real evaluation tool.

It should support:

- rich help
- workflow help
- LLM judge help
- scoring help
- examples help
- colorful but optional terminal output
- no-color/plain/json modes
- progress display
- score tables
- warning panels
- improvement checklists
- doctor command
- clear distinction between profile-only, deterministic run, and LLM-judged run
