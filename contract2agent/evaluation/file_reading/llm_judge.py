from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from contract2agent.evaluation.file_reading.graders import (
    citation_actual_text,
    grade_run,
    load_run,
)
from contract2agent.evaluation.file_reading.schema import (
    Citation,
    CorpusManifest,
    EvidenceSpan,
    FileReadingGrade,
    FileReadingJudgeInput,
    FileReadingJudgeOutput,
    FileReadingJudgeReport,
    FileReadingJudgeTaskResult,
    FileReadingRun,
    FileReadingTask,
    TargetAgentOutput,
    from_dict,
    to_dict,
)
from contract2agent.evaluation.file_reading.tasks import load_tasks_jsonl


JUDGE_PROMPT_VERSION = "file_reading_semantic_judge_v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"

SEMANTIC_TASK_TYPES = {
    "single_file_qa",
    "multi_file_qa",
    "citation_required_qa",
    "conflicting_evidence",
    "version_comparison",
    "summary_with_citations",
    "unanswerable_question",
}

APPROX_MODEL_RATES_USD_PER_MILLION_TOKENS = {
    # Conservative defaults used only for pre-call budget estimates. Actual API
    # responses may include usage data and users can override budgets per run.
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}

JUDGE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "semantic_correctness_score",
        "evidence_support_score",
        "contradiction_risk",
        "unsupported_claims",
        "missing_evidence_notes",
        "recommendation_items",
        "confidence",
        "rationale",
        "limitations",
        "judge_model",
        "judge_provider",
        "judge_based",
        "deterministic",
    ],
    "properties": {
        "semantic_correctness_score": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_support_score": {"type": "number", "minimum": 0, "maximum": 1},
        "contradiction_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "missing_evidence_notes": {"type": "array", "items": {"type": "string"}},
        "recommendation_items": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale": {"type": "string"},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "judge_model": {"type": "string"},
        "judge_provider": {"type": "string"},
        "judge_based": {"type": "boolean"},
        "deterministic": {"type": "boolean"},
    },
}


@dataclass
class JudgeOptions:
    provider: str = "none"
    model: str = DEFAULT_OPENAI_MODEL
    judge_command: str = ""
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL
    api_key_env: str = DEFAULT_API_KEY_ENV
    api_key: str | None = None
    prompt_for_key: bool = False
    interactive: bool = False
    judge_only: str = "failed"
    max_judge_tasks: int = 20
    max_input_chars: int = 12000
    max_output_tokens: int = 500
    evidence_snippet_limit: int = 5
    cost_budget_usd: float | None = None
    dry_run_cost_estimate: bool = False
    cache_judge_results: bool = True
    cache_dir: str | Path | None = None
    timeout_seconds: float = 60.0


@dataclass
class ProviderResponse:
    output: FileReadingJudgeOutput
    token_usage: dict[str, Any]


class JudgeProvider:
    provider_name = "none"

    def judge(
        self,
        judge_input: FileReadingJudgeInput,
        *,
        options: JudgeOptions,
        run_dir: Path,
    ) -> ProviderResponse:
        raise NotImplementedError


class CommandJudgeProvider(JudgeProvider):
    provider_name = "command"

    def __init__(self, command: str) -> None:
        if "{input_json}" not in command or "{output_json}" not in command:
            raise ValueError("--judge-command must include {input_json} and {output_json}")
        self.command = command

    def judge(
        self,
        judge_input: FileReadingJudgeInput,
        *,
        options: JudgeOptions,
        run_dir: Path,
    ) -> ProviderResponse:
        with tempfile.TemporaryDirectory(prefix="c2a-file-judge-", dir=run_dir) as tmp:
            input_path = Path(tmp) / "judge_input.json"
            output_path = Path(tmp) / "judge_output.json"
            input_path.write_text(
                json.dumps(to_dict(judge_input), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            command = _command_args(self.command, input_path, output_path)
            completed = subprocess.run(
                command,
                cwd=run_dir,
                text=True,
                capture_output=True,
                timeout=options.timeout_seconds,
                shell=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"judge command failed with exit code {completed.returncode}: "
                    f"{completed.stderr.strip()[:500]}"
                )
            try:
                data = json.loads(output_path.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise RuntimeError("judge command did not write {output_json}") from exc
        return ProviderResponse(
            output=validate_judge_output(
                data,
                provider=self.provider_name,
                model=options.model,
            ),
            token_usage={},
        )


class OpenAICompatibleJudgeProvider(JudgeProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, *, base_url: str = DEFAULT_OPENAI_BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def judge(
        self,
        judge_input: FileReadingJudgeInput,
        *,
        options: JudgeOptions,
        run_dir: Path,
    ) -> ProviderResponse:
        del run_dir
        payload = {
            "model": options.model,
            "temperature": 0,
            "max_completion_tokens": options.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "file_reading_judge_output",
                    "strict": True,
                    "schema": JUDGE_OUTPUT_SCHEMA,
                },
            },
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an optional non-deterministic evaluator for file-reading "
                        "agent outputs. Return strict JSON only. Do not grade citation "
                        "span existence, path containment, schema compliance, timeouts, "
                        "or forbidden-file safety; those are deterministic checks."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(to_dict(judge_input), sort_keys=True),
                },
            ],
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=options.timeout_seconds) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"OpenAI-compatible judge request failed: HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI-compatible judge request failed: {exc.reason}") from exc

        content = (
            response_data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        try:
            output_data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"OpenAI-compatible judge returned non-JSON content: {exc.msg}") from exc
        usage = response_data.get("usage", {})
        return ProviderResponse(
            output=validate_judge_output(output_data, provider=self.provider_name, model=options.model),
            token_usage=usage if isinstance(usage, dict) else {},
        )


def resolve_api_key(
    *,
    provider: str,
    api_key: str | None = None,
    api_key_env: str = DEFAULT_API_KEY_ENV,
    prompt_for_key: bool = False,
    interactive: bool = False,
    getpass_func: Callable[[str], str] = getpass.getpass,
) -> str | None:
    if normalize_provider(provider) != "openai":
        return None
    if api_key:
        return api_key
    env_value = os.environ.get(api_key_env)
    if env_value:
        return env_value
    if prompt_for_key:
        if not interactive:
            raise RuntimeError(
                f"{api_key_env} is not set and hidden API key input is only available in an interactive terminal."
            )
        entered = getpass_func(f"{api_key_env} (hidden, session only): ")
        return entered or None
    return None


def normalize_provider(provider: str) -> str:
    normalized = provider.casefold().strip()
    if normalized in {"none", "deterministic", ""}:
        return "none"
    if normalized in {"llm", "openai", "openai-compatible"}:
        return "openai"
    if normalized in {"command", "cmd", "local-command"}:
        return "command"
    raise ValueError("--provider must be none, deterministic, command, llm, or openai")


def provider_from_options(options: JudgeOptions) -> JudgeProvider | None:
    provider = normalize_provider(options.provider)
    if provider == "none":
        return None
    if provider == "command":
        return CommandJudgeProvider(options.judge_command)
    api_key = resolve_api_key(
        provider=provider,
        api_key=options.api_key,
        api_key_env=options.api_key_env,
        prompt_for_key=options.prompt_for_key,
        interactive=options.interactive,
    )
    if not api_key:
        raise RuntimeError(
            f"{options.api_key_env} is not configured. Set it, pass a session key interactively, "
            "or use --provider command with --judge-command."
        )
    return OpenAICompatibleJudgeProvider(api_key, base_url=options.openai_base_url)


def validate_judge_output(
    data: Any,
    *,
    provider: str,
    model: str,
) -> FileReadingJudgeOutput:
    if not isinstance(data, dict):
        raise ValueError("Judge output must be a JSON object.")
    required = set(JUDGE_OUTPUT_SCHEMA["required"])
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"Judge output missing required field(s): {', '.join(missing)}")
    for field in (
        "semantic_correctness_score",
        "evidence_support_score",
        "contradiction_risk",
        "confidence",
    ):
        value = data.get(field)
        if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            raise ValueError(f"Judge output {field} must be a number between 0 and 1.")
        data[field] = round(float(value), 3)
    for field in (
        "unsupported_claims",
        "missing_evidence_notes",
        "recommendation_items",
        "limitations",
    ):
        if not isinstance(data.get(field), list) or not all(isinstance(item, str) for item in data[field]):
            raise ValueError(f"Judge output {field} must be a list of strings.")
    for field in ("rationale", "judge_model", "judge_provider"):
        if not isinstance(data.get(field), str):
            raise ValueError(f"Judge output {field} must be a string.")
    if data.get("judge_based") is not True:
        raise ValueError("Judge output judge_based must be true.")
    if data.get("deterministic") is not False:
        raise ValueError("Judge output deterministic must be false.")
    data.setdefault("judge_provider", provider)
    data.setdefault("judge_model", model)
    if not data["judge_provider"]:
        data["judge_provider"] = provider
    if not data["judge_model"]:
        data["judge_model"] = model
    return from_dict(FileReadingJudgeOutput, data)


def build_judge_input(
    *,
    run: FileReadingRun,
    task: FileReadingTask,
    output: TargetAgentOutput,
    grade: FileReadingGrade,
    max_input_chars: int = 12000,
    evidence_snippet_limit: int = 5,
) -> FileReadingJudgeInput:
    manifest = run.corpus_manifest
    task_forbidden = set(task.forbidden_files)
    cited_snippets = _cited_snippets(
        output.citations,
        manifest,
        limit=evidence_snippet_limit,
        blocked_files=task_forbidden,
    )
    gold_evidence = _gold_evidence(
        task.gold_evidence_spans or task.expected_citations,
        manifest,
        limit=evidence_snippet_limit,
        blocked_files=task_forbidden,
    )
    judge_input = FileReadingJudgeInput(
        task_id=task.task_id,
        task_type=task.task_type,
        question=_sanitize_text(task.question, manifest),
        agent_answer=_sanitize_text(output.answer, manifest),
        agent_citations=[
            {
                "file_id": citation.file_id,
                "line_start": citation.line_start,
                "line_end": citation.line_end,
                "quote": _sanitize_text(citation.quote, manifest),
            }
            for citation in output.citations
            if _file_allowed_for_judge(citation.file_id, manifest, blocked_files=task_forbidden)
        ],
        cited_snippets=cited_snippets,
        gold_answer=_sanitize_text(task.gold_answer, manifest),
        gold_evidence=gold_evidence,
        deterministic_grade_summary={
            "total_score": grade.total_score,
            "answer_score": grade.answer_score,
            "citation_score": grade.citation_score,
            "citation_presence": grade.citation_presence,
            "citation_span_accuracy": grade.citation_span_accuracy,
            "citation_quote_match": grade.citation_quote_match,
            "supporting_file_recall": grade.supporting_file_recall,
            "supporting_file_precision": grade.supporting_file_precision,
            "unanswerable_abstention_score": grade.unanswerable_abstention_score,
            "unsupported_claim_rate": grade.unsupported_claim_rate,
            "schema_score": grade.schema_score,
        },
        failure_modes=list(grade.failures),
        judge_instructions=(
            "Evaluate semantic answer correctness, evidence-to-answer support, open-ended "
            "answer quality, summary faithfulness, contradiction risk, and actionable "
            "recommendations. Do not override deterministic citation span, forbidden-file, "
            "schema, timeout, hash, or path checks."
        ),
        metadata={
            "prompt_version": JUDGE_PROMPT_VERSION,
            "deterministic_first": True,
            "full_corpus_included": False,
        },
    )
    return compact_judge_input(judge_input, max_input_chars=max_input_chars)


def compact_judge_input(
    judge_input: FileReadingJudgeInput,
    *,
    max_input_chars: int,
) -> FileReadingJudgeInput:
    data = to_dict(judge_input)
    if _json_chars(data) <= max_input_chars:
        return judge_input
    trimmed = from_dict(FileReadingJudgeInput, data)
    trimmed.cited_snippets = trimmed.cited_snippets[:2]
    trimmed.gold_evidence = trimmed.gold_evidence[:2]
    trimmed.agent_answer = _truncate(trimmed.agent_answer, 2500)
    trimmed.question = _truncate(trimmed.question, 1200)
    trimmed.metadata = {**trimmed.metadata, "truncated_for_budget": True}
    while _json_chars(to_dict(trimmed)) > max_input_chars and trimmed.cited_snippets:
        trimmed.cited_snippets.pop()
    while _json_chars(to_dict(trimmed)) > max_input_chars and trimmed.gold_evidence:
        trimmed.gold_evidence.pop()
    if _json_chars(to_dict(trimmed)) > max_input_chars:
        trimmed.agent_answer = _truncate(trimmed.agent_answer, 1000)
    return trimmed


def select_tasks_for_judging(
    grades: list[FileReadingGrade],
    tasks: list[FileReadingTask],
    *,
    judge_only: str,
    max_judge_tasks: int,
) -> list[FileReadingTask]:
    mode = judge_only.casefold().strip()
    if mode not in {"failed", "uncertain", "open-ended", "open_ended", "all"}:
        raise ValueError("--judge-only must be failed, uncertain, open-ended, or all")
    if max_judge_tasks <= 0:
        return []
    grade_by_id = {grade.task_id: grade for grade in grades}
    selected: list[FileReadingTask] = []
    for task in tasks:
        grade = grade_by_id.get(task.task_id)
        if grade is None:
            continue
        if mode == "all":
            selected.append(task)
        elif mode == "failed" and (grade.failures or grade.total_score < 0.8):
            selected.append(task)
        elif mode == "uncertain" and (
            0.35 <= grade.total_score <= 0.85
            or grade.unsupported_claim_rate > 0
            or "answer_incorrect" in grade.failures
        ):
            selected.append(task)
        elif mode in {"open-ended", "open_ended"} and task.task_type in SEMANTIC_TASK_TYPES:
            selected.append(task)
        if max_judge_tasks >= 0 and len(selected) >= max_judge_tasks:
            break
    return selected


def judge_cache_key(
    judge_input: FileReadingJudgeInput,
    *,
    provider: str,
    model: str,
    prompt_version: str = JUDGE_PROMPT_VERSION,
) -> str:
    payload = {
        "judge_input": to_dict(judge_input),
        "provider": normalize_provider(provider),
        "model": model,
        "prompt_version": prompt_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def estimate_request(
    judge_input: FileReadingJudgeInput,
    *,
    model: str,
    max_output_tokens: int,
) -> tuple[int, float]:
    input_chars = _json_chars(to_dict(judge_input))
    input_tokens = max(1, (input_chars + 3) // 4)
    rates = APPROX_MODEL_RATES_USD_PER_MILLION_TOKENS.get(
        model,
        {"input": 0.50, "output": 2.00},
    )
    cost = (
        input_tokens * rates["input"] / 1_000_000
        + max_output_tokens * rates["output"] / 1_000_000
    )
    return input_tokens, round(cost, 6)


def run_judge(
    run: FileReadingRun | str | Path,
    tasks: list[FileReadingTask] | str | Path | None = None,
    *,
    options: JudgeOptions,
    out: str | Path | None = None,
) -> FileReadingJudgeReport:
    loaded_run = load_run(run) if isinstance(run, (str, Path)) else run
    run_dir = Path(run).resolve() if isinstance(run, (str, Path)) else Path(".").resolve()
    if run_dir.is_file():
        run_dir = run_dir.parent
    loaded_tasks = (
        tasks
        if isinstance(tasks, list)
        else load_tasks_jsonl(tasks)
        if tasks is not None
        else loaded_run.tasks
    )
    grades, scorecard = grade_run(loaded_run, loaded_tasks)
    provider_name = normalize_provider(options.provider)
    selected_tasks = select_tasks_for_judging(
        grades,
        loaded_tasks,
        judge_only=options.judge_only,
        max_judge_tasks=options.max_judge_tasks,
    )
    grade_by_id = {grade.task_id: grade for grade in grades}
    task_by_id = {task.task_id: task for task in loaded_tasks}
    output_by_id = loaded_run.outputs
    cache_dir = Path(options.cache_dir) if options.cache_dir is not None else run_dir / ".judge_cache"
    if options.cache_judge_results:
        cache_dir.mkdir(parents=True, exist_ok=True)
    provider = None
    if provider_name != "none" and not options.dry_run_cost_estimate:
        provider = provider_from_options(options)

    results: list[FileReadingJudgeTaskResult] = []
    total_estimated_cost = 0.0
    selected_ids = {task.task_id for task in selected_tasks}
    calls_made = 0
    cache_hits = 0
    budget_skips = 0
    dry_run_skips = 0
    failures: list[str] = []
    for task in loaded_tasks:
        grade = grade_by_id.get(task.task_id)
        if grade is None:
            continue
        if task.task_id not in selected_ids:
            results.append(
                FileReadingJudgeTaskResult(
                    task_id=task.task_id,
                    selected=False,
                    status="not_selected",
                    provider=provider_name,
                    model=options.model,
                    prompt_version=JUDGE_PROMPT_VERSION,
                    deterministic_total_score=grade.total_score,
                )
            )
            continue
        output = output_by_id.get(task.task_id, TargetAgentOutput(errors=["missing output"]))
        judge_input = build_judge_input(
            run=loaded_run,
            task=task,
            output=output,
            grade=grade,
            max_input_chars=options.max_input_chars,
            evidence_snippet_limit=options.evidence_snippet_limit,
        )
        input_chars = _json_chars(to_dict(judge_input))
        input_tokens, estimated_cost = estimate_request(
            judge_input,
            model=options.model,
            max_output_tokens=options.max_output_tokens,
        )
        key = judge_cache_key(judge_input, provider=provider_name, model=options.model)
        result = FileReadingJudgeTaskResult(
            task_id=task.task_id,
            selected=True,
            status="selected",
            cache_key=key,
            provider=provider_name,
            model=options.model,
            prompt_version=JUDGE_PROMPT_VERSION,
            input_chars=input_chars,
            estimated_input_tokens=input_tokens,
            max_output_tokens=options.max_output_tokens,
            estimated_cost_usd=estimated_cost,
            deterministic_total_score=grade.total_score,
        )
        if options.cost_budget_usd is not None and total_estimated_cost + estimated_cost > options.cost_budget_usd:
            result.status = "skipped_budget"
            result.warnings.append("Skipped before API call because estimated cost would exceed --cost-budget-usd.")
            budget_skips += 1
            results.append(result)
            continue
        total_estimated_cost += estimated_cost
        cache_path = cache_dir / f"{key}.json"
        if options.cache_judge_results and cache_path.exists():
            try:
                cached = from_dict(
                    FileReadingJudgeTaskResult,
                    json.loads(cache_path.read_text(encoding="utf-8")),
                )
                cached.status = "cache_hit"
                results.append(cached)
                cache_hits += 1
                continue
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                result.warnings.append(f"Ignored invalid judge cache entry: {type(exc).__name__}")
        if provider_name == "none":
            result.status = "deterministic_only"
            result.warnings.append("No judge provider selected; deterministic grades remain the source of truth.")
            results.append(result)
            continue
        if options.dry_run_cost_estimate:
            result.status = "dry_run_estimate"
            result.warnings.append("Dry run only; no judge command or API call was made.")
            dry_run_skips += 1
            results.append(result)
            continue
        try:
            assert provider is not None
            provider_response = provider.judge(judge_input, options=options, run_dir=run_dir)
            result.judge_output = provider_response.output
            result.token_usage = provider_response.token_usage
            result.status = "completed"
            calls_made += 1
            if options.cache_judge_results:
                cache_path.write_text(
                    json.dumps(to_dict(result), indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
        except Exception as exc:
            result.status = "judge_failed"
            result.error = f"{type(exc).__name__}: {_sanitize_local_paths(str(exc))}"
            result.warnings.append("Fell back to deterministic grade for this task.")
            failures.append(f"{task.task_id}: {result.error}")
        results.append(result)

    report = FileReadingJudgeReport(
        run_id=loaded_run.run_id,
        judge_provider=provider_name,
        judge_model=options.model,
        prompt_version=JUDGE_PROMPT_VERSION,
        deterministic_scorecard=to_dict(scorecard),
        judge_only=options.judge_only,
        max_judge_tasks=options.max_judge_tasks,
        cost_budget_usd=options.cost_budget_usd,
        dry_run_cost_estimate=options.dry_run_cost_estimate,
        summary={
            "tasks_total": len(loaded_tasks),
            "tasks_selected": len(selected_tasks),
            "calls_made": calls_made,
            "cache_hits": cache_hits,
            "skipped_due_to_budget": budget_skips,
            "dry_run_estimates": dry_run_skips,
            "estimated_cost_usd": round(total_estimated_cost, 6),
            "deterministic_default": True,
            "api_calls_require_explicit_judge": True,
        },
        results=results,
        failures=failures,
        limitations=[
            "LLM judge results are optional, judge-based, and non-deterministic.",
            "Deterministic citation, forbidden-file, schema, timeout, hash, and path checks remain authoritative.",
            "Judge inputs include compact task/output/evidence context only, not the full corpus.",
        ],
    )
    if out is not None:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(to_dict(report), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def load_judge_report(path: str | Path) -> FileReadingJudgeReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return from_dict(FileReadingJudgeReport, data)


def llm_configuration_status(
    *,
    provider: str,
    api_key_env: str = DEFAULT_API_KEY_ENV,
    judge_command: str = "",
) -> dict[str, Any]:
    provider_name = normalize_provider(provider)
    status = {
        "provider": provider_name,
        "api_calls_enabled": provider_name == "openai",
        "api_key_env": api_key_env,
        "api_key_configured": bool(os.environ.get(api_key_env)),
        "api_key_value": None,
        "command_configured": bool(judge_command),
        "safe_to_print": True,
    }
    if provider_name == "command" and judge_command:
        status["command_has_input_placeholder"] = "{input_json}" in judge_command
        status["command_has_output_placeholder"] = "{output_json}" in judge_command
    return status


def _cited_snippets(
    citations: list[Citation],
    manifest: CorpusManifest,
    *,
    limit: int,
    blocked_files: set[str] | None = None,
) -> list[dict[str, Any]]:
    snippets: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None, int | None]] = set()
    for citation in citations:
        if len(snippets) >= limit:
            break
        if not _file_allowed_for_judge(citation.file_id, manifest, blocked_files=blocked_files):
            continue
        key = (citation.file_id, citation.line_start, citation.line_end)
        if key in seen:
            continue
        seen.add(key)
        text = citation_actual_text(citation, manifest)
        snippets.append(
            {
                "file_id": citation.file_id,
                "line_start": citation.line_start,
                "line_end": citation.line_end,
                "quote": _truncate(_sanitize_text(citation.quote, manifest), 1200),
                "snippet": _truncate(_sanitize_text(text, manifest), 1600),
            }
        )
    return snippets


def _gold_evidence(
    spans: list[EvidenceSpan],
    manifest: CorpusManifest,
    *,
    limit: int,
    blocked_files: set[str] | None = None,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for span in spans:
        if len(evidence) >= limit:
            break
        if not _file_allowed_for_judge(span.file_id, manifest, blocked_files=blocked_files):
            continue
        citation = Citation(
            file_id=span.file_id,
            line_start=span.line_start,
            line_end=span.line_end,
            quote=span.quote,
        )
        text = span.quote or citation_actual_text(citation, manifest)
        evidence.append(
            {
                "file_id": span.file_id,
                "line_start": span.line_start,
                "line_end": span.line_end,
                "quote": _truncate(_sanitize_text(text, manifest), 1600),
                "label": span.label,
            }
        )
    return evidence


def _file_allowed_for_judge(
    file_id: str,
    manifest: CorpusManifest,
    *,
    blocked_files: set[str] | None = None,
) -> bool:
    if blocked_files and file_id in blocked_files:
        return False
    forbidden = set(manifest.forbidden_files)
    allowed = set(manifest.allowed_files)
    if file_id in forbidden:
        return False
    if allowed and file_id not in allowed:
        return False
    document = {item.file_id: item for item in manifest.documents}.get(file_id)
    return document is None or document.allowed


def _sanitize_text(value: str, manifest: CorpusManifest) -> str:
    sanitized = value.replace(str(manifest.root_path), "<corpus_root>")
    sanitized = sanitized.replace(str(Path(manifest.root_path).resolve()), "<corpus_root>")
    sanitized = _redact_secret_like_text(sanitized)
    sanitized = sanitized.replace("\\", "/")
    parts = sanitized.split()
    cleaned = []
    for part in parts:
        lowered = part.casefold()
        if ":/" in part and len(part) > 3:
            cleaned.append("<local_path>")
        elif lowered.startswith(("/users/", "/home/", "/var/", "/tmp/")):
            cleaned.append("<local_path>")
        else:
            cleaned.append(part)
    return " ".join(cleaned)


_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[:=]\s*[^\s,;`'\"<>]+"
)
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


def _redact_secret_like_text(value: str) -> str:
    redacted = _SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=<redacted_secret>", value)
    return _OPENAI_KEY_RE.sub("<redacted_secret>", redacted)


def _json_chars(data: Any) -> int:
    return len(json.dumps(data, sort_keys=True, separators=(",", ":")))


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 16)].rstrip() + " ... [truncated]"


def _command_args(command: str, input_path: Path, output_path: Path) -> list[str]:
    parts = shlex.split(command, posix=os.name != "nt")
    return [
        _strip_wrapping_quotes(part)
        .replace("{input_json}", str(input_path))
        .replace("{output_json}", str(output_path))
        for part in parts
    ]


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


_WINDOWS_PATH_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s`\"'<>|]+")
_POSIX_LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])/(?:Users|home|var|tmp)/[^\s`\"'<>|]+")


def _sanitize_local_paths(value: str) -> str:
    sanitized = _WINDOWS_PATH_RE.sub("<local_path>", value)
    return _POSIX_LOCAL_PATH_RE.sub("<local_path>", sanitized)
