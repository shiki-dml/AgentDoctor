# File Reading Eval Examples

This directory contains small, intentional fixtures for the `c2a file-eval` CLI. They are safe to run locally and do not require API calls.

## Deterministic Run

```bash
c2a file-eval import-local --input examples/file_reading_eval/corpus --out .runs/example-corpus --manifest .runs/example-corpus/manifest.json
c2a file-eval validate --corpus .runs/example-corpus/manifest.json --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl
c2a file-eval run --profile examples/file_reading_eval/profiles/good_file_reader.json --agent-command "python examples/file_reading_eval/agents/dummy_good_reader.py {input_json} {output_json}" --corpus .runs/example-corpus/manifest.json --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl --out .runs/example-good
c2a file-eval grade --run .runs/example-good --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl --out .runs/example-good/grades.json
c2a file-eval report --run .runs/example-good --format md,json --out .runs/example-report
```

## Profile-Only Mode

```bash
c2a file-eval profile-only --profile examples/file_reading_eval/profiles/weak_file_reader.json --out .runs/profile-only
```

Profile-only output is readiness analysis. It does not claim observed reading performance.

## Optional LLM Judge Dry Run

```bash
c2a file-eval judge --run .runs/example-good --provider openai --dry-run-cost-estimate --judge-only failed --max-judge-tasks 3
```

This estimates request size and cost. It does not call an API.

## Command-Based Judge

```bash
c2a file-eval judge --run .runs/example-good --provider command --judge-command "python examples/file_reading_eval/agents/dummy_command_judge.py {input_json} {output_json}"
```

The command adapter is useful for local/custom judges and CI tests because it avoids provider-specific API dependencies.

## Failure Fixtures

- `dummy_bad_citation_reader.py`: returns the right answer with an incorrect quote.
- `dummy_forbidden_reader.py`: records a forbidden file in `files_read`.
- `dummy_timeout_reader.py`: sleeps long enough to trip short task budgets.

Use `citation_tasks.jsonl`, `unanswerable_tasks.jsonl`, and `distractor_tasks.jsonl` to exercise citation mismatch, abstention, distractor resistance, forbidden file behavior, reference comparison, and report generation.
