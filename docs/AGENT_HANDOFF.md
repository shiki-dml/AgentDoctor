# Agent Handoff

Last updated: 2026-05-14

## Current Status

- Project root: `D:\Projects\Contract2Agent`
- Repository root from git: `D:/Projects/Contract2Agent`
- Branch observed during this task: `codex/refine-cost-privacy-cleanup`
- Shell/environment: Windows PowerShell 5.1.26100.8115
- Current task: apply the Reflexion idea globally to agent evaluation and
  repo-local agent organization, then add a minimal preview-only
  `program-correct` command using existing agents and Patch Preview.
- Added feature: `eval-agent` reports now include a deterministic global
  Reflexion update plan that converts evaluator feedback, weak score
  dimensions, missing evidence, and risk flags into next-episode verbal memory.
- API behavior: no API call is made and no API key is required. The report
  states that any future LLM reflector must collect credentials from an
  environment variable or hidden session-only prompt and never persist them.
- Agent tooling change: `.codex/config.toml` active roles were reduced to
  `codebase_mapper`, `contract_generator`, `feature_generator`, `evaluator`,
  `bug_reviewer`, and `handoff_writer`. Former inventory/planner/docs-specialist
  role files remain as historical references but are not active by default.
- Added feature: `program-correct` is a thin CLI wrapper around Patch Preview.
  It reports the existing correction agent loop
  `codebase_mapper -> contract_generator -> feature_generator ->
  bug_reviewer/evaluator -> handoff_writer` and writes preview-only artifacts
  under `.agentdoctor/program-correction/`.
- Feature registry: not changed; no new feature was marked verified from this
  task.

## Baseline Results

| Command | Result |
| --- | --- |
| `git status --short` | Initial sandboxed attempt failed with `windows sandbox: setup refresh failed`; escalated retry returned clean output. |
| `docs/AGENT_HANDOFF.md`, `docs/harness/PROGRESS.md`, `docs/ARCHITECTURE.md`, `docs/CODEMAP.md`, `docs/PROJECT_CONTEXT.md`, `docs/GOLDEN_PRINCIPLES.md` | Read before edits. |
| `.agents/skills/agent-eval-architect/SKILL.md` | Read and followed for global eval-framework boundaries. |
| `.agents/skills/research-grounded-eval/SKILL.md` | Read and followed for external research/reference discipline. |
| `.agents/skills/codex-tooling-orchestrator/SKILL.md` | Read and followed for repo-local Codex role/config changes. |

## Sources Consulted

- `https://arxiv.org/abs/2303.11366`
- `https://github.com/noahshinn/reflexion`

## Files Updated In This Task

- `.agents/skills/codex-tooling-orchestrator/SKILL.md`
- `.codex/config.toml`
- `AGENTS.md`
- `README.md`
- `contract2agent/evaluation/README.md`
- `contract2agent/evaluation/__init__.py`
- `contract2agent/evaluation/reflexion.py`
- `contract2agent/cli.py`
- `contract2agent/README.md`
- `contract2agent/evaluation/registry.py`
- `contract2agent/evaluation/reports.py`
- `contract2agent/evaluation/schema.py`
- `docs/ARCHITECTURE.md`
- `docs/CODEMAP.md`
- `docs/GOLDEN_PRINCIPLES.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/cli.md`
- `docs/data/agent_eval/source_references.json`
- `docs/harness/EVAL_MATRIX.md`
- `docs/harness/README.md`
- `examples/agent_eval/benchmark_references.json`
- `tests/test_agent_evaluation_framework.py`
- `tests/test_patch_preview.py`
- `docs/AGENT_HANDOFF.md`
- `docs/harness/PROGRESS.md`

## What Changed

- Added `ReflexionUpdate` and `ReflexionUpdatePlan` schemas.
- Added `contract2agent/evaluation/reflexion.py`, a deterministic global update
  builder. It does not call an LLM, mutate weights, execute agents, or import
  benchmark scores.
- Integrated the update plan into Markdown and JSON reports through
  `ReportRenderer`.
- Added Reflexion as contextual methodology metadata only.
- Updated docs to describe Reflexion updates as global verbal memory, separate
  from observed evidence, prediction, and scores.
- Trimmed the active repo-local Codex role registry to a smaller Reflexion-like
  loop: context mapper, contract scoper, actor, evaluator/reviewer feedback,
  and handoff memory.
- Added the smallest possible `program-correct` implementation: no new package,
  no new models, and no auto-apply path. The command delegates to
  `patch-preview` and changes only CLI routing/output defaults.

## Validation Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile contract2agent\evaluation\schema.py contract2agent\evaluation\reflexion.py contract2agent\evaluation\reports.py` | Passed | No output. |
| `python -m pytest tests\test_agent_evaluation_framework.py` | Passed | 22 tests passed. |
| `python -m pytest tests\test_patch_preview.py` | Passed | 27 tests passed. |
| `python -m compileall -q contract2agent tests scripts` | Passed | No output. |
| `python -m py_compile contract2agent\cli.py` | Passed | No output. |
| `python -c "import pathlib, tomllib; tomllib.loads(pathlib.Path('.codex/config.toml').read_text(encoding='utf-8')); print('toml ok')"` | Passed | Printed `toml ok`. |
| `python scripts\check_docs_links.py` | Passed | Checked 65 Markdown files; all relative links resolve. |
| `python scripts\harness\validate_docs.py` | Passed | Validated required docs, module READMEs, AGENTS length, and feature registry shape. |
| `python -m contract2agent.cli eval-agent --profile examples\agent_eval\coding_agent_profile.json --results examples\agent_eval\sample_experiment_results.json --benchmarks examples\agent_eval\benchmark_references.json --out .runs\reflexion-agent-eval.md` | Passed | Wrote an agent evaluation report with the new Reflexion section. |
| `python -m contract2agent.cli program-correct --from-run .tmp_pytest_base\contract2agent-test-runs\patch_preview\program_correct_*\.agentdoctor\runs\latest.json --project-root .` | Passed with skipped findings | PowerShell did not expand the wildcard; command exited 0, wrote preview artifacts, and reported the missing input honestly. Artifacts were deleted after inspection. |
| `python -m pytest` | Passed | 367 tests passed. |
| `python -m mkdocs build --strict` | Passed | Built docs into `site/`. |
| `git diff --check` | Passed | No whitespace errors. |

## Known Risks

- The Reflexion plan is deterministic guidance only. It is not an observed
  improvement, agent execution trace, benchmark result, or model update.
- The upstream Reflexion project was consulted as a methodology reference only;
  no upstream code, dataset, or result was vendored.
- Former `.codex/agents/*.toml` role files were not physically deleted, only
  removed from the active `.codex/config.toml` registry to preserve history.
- `program-correct` does not repair code by itself. It creates a correction
  plan/preview for existing agent roles and reuses Patch Preview safety rules.
- Generated `.runs/reflexion-agent-eval.md` and `site/` are validation artifacts
  and should remain ignored.

## Recommended Next Codex Prompt

```text
Use the evaluator role. Review the Reflexion update-plan diff for evidence
separation, API-key safety, and whether the reduced active Codex role set is
consistent with AGENTS.md and .codex/config.toml. Do not modify files.
```
