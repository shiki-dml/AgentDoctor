# File-Reading Agent Evaluation

## Overview

Contract2Agent includes a specialized `file_reading_agent` subsystem for observed local evaluation. It imports approved corpora, loads or builds tasks, runs a target agent through a command adapter, captures artifacts, grades deterministic dimensions, optionally adds an LLM judge, compares compatible reference results, and renders Markdown/JSON reports.

## Why Observed Evaluation Matters

File-reading claims are not performance evidence. A profile-only report can describe readiness, risk, and an eval plan, but actual reading performance requires observed outputs, citations, traces, and grading artifacts.

## Deterministic vs LLM-Judged Evaluation

Deterministic grading is the default and requires no API. It scores answer correctness, citation presence, quote match, line span accuracy, file selection, forbidden-file safety, abstention, schema compliance, latency, and unsupported-claim proxies.

LLM judging is optional, explicit, non-deterministic, and supplementary. It can help with semantic equivalence, summary faithfulness, contradiction detection, evidence support, and recommendation synthesis. It does not replace deterministic checks for citations, forbidden files, schema, paths, hashes, or timeouts.

## Installation And Setup

```bash
python -m pip install -e ".[dev]"
c2a file-eval doctor
c2a file-eval help workflow
```

## Quick Start

```bash
c2a file-eval import-local --input examples/file_reading_eval/corpus --out .runs/file-corpus --manifest .runs/file-corpus/manifest.json
c2a file-eval validate --corpus .runs/file-corpus/manifest.json --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl
c2a file-eval run --profile examples/file_reading_eval/profiles/good_file_reader.json --agent-command "python examples/file_reading_eval/agents/dummy_good_reader.py {input_json} {output_json}" --corpus .runs/file-corpus/manifest.json --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl --out .runs/file-run
c2a file-eval grade --run .runs/file-run --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl --out .runs/file-run/grades.json
c2a file-eval report --run .runs/file-run --format md,json --out .runs/file-report
```

## CLI Command Reference

- `init`: create a starter workspace layout.
- `import-local`: import local text files or papers with provenance metadata.
- `build-tasks`: generate deterministic smoke tasks.
- `validate`: check task IDs, file references, evidence, and answerability metadata.
- `run`: execute a target agent command with `{input_json}` and `{output_json}` placeholders.
- `grade`: compute deterministic grades and scorecards.
- `judge`: run optional semantic judging after deterministic grading.
- `compare`: compare against compatible reference results.
- `report`: render Markdown/JSON reports.
- `doctor`: print environment and safety checks.

## Help Commands

```bash
c2a file-eval --help
c2a file-eval help
c2a file-eval help workflow
c2a file-eval help deterministic
c2a file-eval help llm
c2a file-eval help scoring
c2a file-eval help examples
c2a file-eval help references
```

## Corpus Import

`import-local` copies supported text-like files into a corpus directory and writes a manifest. Secret-like paths, `.env`, cache directories, virtual environments, and unsupported files are skipped. Network imports are disabled unless a command explicitly supports and receives `--allow-network`.

## Task Files

Tasks are JSONL records with `task_id`, `task_type`, `question`, allowed/forbidden files, supporting files, gold answers, evidence spans, and unanswerable flags. Keep tasks general and avoid exact fixture-name logic.

## Running A Target Agent

The runner sends JSON containing the task, corpus directory, manifest path, allowed files, forbidden files, instructions, and required output schema. The target agent returns JSON with `answer`, `citations`, `confidence`, `files_read`, and optional notes.

## Grading

Deterministic graders run first. They produce per-task grades and a scorecard by dimension. Reports keep deterministic scores separate from optional judge results.

## Optional LLM Judge

Use an LLM judge only when requested:

```bash
c2a file-eval judge --run .runs/file-run --provider openai --judge-only failed --max-judge-tasks 5 --cost-budget-usd 1.00
```

For local/custom judges:

```bash
c2a file-eval judge --run .runs/file-run --provider command --judge-command "python examples/file_reading_eval/agents/dummy_command_judge.py {input_json} {output_json}"
```

## API Key Handling

The OpenAI-compatible provider reads `OPENAI_API_KEY` by default. If no key is set and the terminal is interactive, `--prompt-for-key` uses hidden session-only input. Keys are never written to reports, logs, cache, browser code, or committed config files.

## Token And Cost Controls

Use:

- `--judge-only failed|uncertain|open-ended|all`
- `--max-judge-tasks N`
- `--llm-max-input-chars N`
- `--llm-max-output-tokens N`
- `--evidence-snippet-limit N`
- `--cost-budget-usd N`
- `--dry-run-cost-estimate`
- `--cache-judge-results` or `--no-judge-cache`

Judge inputs include compact question, answer, citations, cited snippets, gold answer/evidence, deterministic grade summary, failure modes, and instructions. They do not include the full corpus or forbidden files.

## Reference Comparison

Reference results are comparable only when task pack, scoring method, environment, and conditions match. Otherwise they remain contextual evidence and do not produce direct score deltas.

## Report Interpretation

Reports show observed task counts, deterministic score tables, citation quality, file selection, forbidden-file safety, abstention behavior, timeouts, reference compatibility, optional LLM judge status, recommendations, limitations, and trace artifact paths.

## Recommendations

Recommendations are generated from deterministic failure modes first and grouped by priority: critical, high, medium, and low. Optional LLM recommendations can supplement them when judging is enabled, but they are marked as judge-based supplements.

## Examples

See `examples/file_reading_eval/` in the repository for deterministic runs, profile-only mode, LLM judge dry-runs, command-based judges, forbidden-file failures, citation mismatches, unanswerable questions, reference comparison, and report generation.

## Security And Path Boundaries

Do not import secrets or private user files. The importer skips common secret/cache paths. Judge input sanitizes local paths and excludes forbidden files. GitHub Pages remains static and must not call APIs or run arbitrary agent experiments.

## Limitations

- Baseline grading is deterministic but not a full human semantic review.
- LLM judge results are non-deterministic and provider-dependent.
- Public benchmark references are contextual unless comparable observed results exist.
- PDF extraction and network dataset import are intentionally not part of the default dependency-free path.

## Roadmap

- More curated task generators.
- Stronger reference-result compatibility metadata.
- Additional local judge adapters.
- More corpus formats behind explicit optional extras.
