from __future__ import annotations

import json
import re
from pathlib import Path

from contract2agent.evaluation.file_reading.compare import compare_with_references
from contract2agent.evaluation.file_reading.graders import grade_run, load_grades, load_run
from contract2agent.evaluation.file_reading.llm_judge import load_judge_report
from contract2agent.evaluation.file_reading.recommendations import prioritized_recommendations_for_grades
from contract2agent.evaluation.file_reading.runner import load_file_reading_agent_profile
from contract2agent.evaluation.file_reading.schema import (
    ComparisonReport,
    FileReadingAgentProfile,
    FileReadingGrade,
    FileReadingJudgeReport,
    FileReadingRun,
    FileReadingScorecard,
    to_dict,
)


NO_OBSERVED_SCORE_MESSAGE = "No observed performance score because no agent run was executed."


def render_profile_only_report(profile: FileReadingAgentProfile) -> str:
    risks = []
    if profile.can_access_external_paths:
        risks.append("External path access needs strict allowlisting.")
    if profile.can_use_network:
        risks.append("Network access should be disabled during local corpus evaluation unless explicitly required.")
    if profile.can_write_files or profile.can_run_shell:
        risks.append("Write or shell permissions increase boundary risk for a reading-only eval.")
    if not profile.citation_support or profile.citation_support == "unknown":
        risks.append("Citation support is unknown.")
    eval_plan = [
        "Import a local corpus with `c2a file-eval import-local`.",
        "Build deterministic smoke tasks with `c2a file-eval build-tasks`.",
        "Run the target through the JSON adapter with a time/task budget.",
        "Grade and report observed outputs before claiming performance.",
    ]
    lines = [
        "# File Reading Agent Profile Readiness",
        "",
        f"Agent: `{profile.agent_id}` - {profile.name}",
        "",
        NO_OBSERVED_SCORE_MESSAGE,
        "",
        "## Readiness Signals",
        f"- Can list files: {profile.can_list_files}",
        f"- Can search files: {profile.can_search_files}",
        f"- Can read files: {profile.can_read_files}",
        f"- Citation support: {profile.citation_support}",
        f"- Output schema support: {profile.output_schema_support}",
        f"- Trace support: {profile.trace_support}",
        "",
        "## Risks",
    ]
    lines.extend(f"- {risk}" for risk in risks) if risks else lines.append("- No high-risk reading flags declared.")
    lines.extend(["", "## Recommended Eval Plan"])
    lines.extend(f"- {item}" for item in eval_plan)
    lines.extend(
        [
            "",
            "## Limitations",
            "- This report uses profile declarations only.",
            "- Declared capability is not evidence of answer correctness, citation grounding, or safety.",
        ]
    )
    return "\n".join(lines)


def write_profile_only_report(profile_path: str | Path, out_dir: str | Path) -> dict[str, Path]:
    profile = load_file_reading_agent_profile(profile_path)
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    markdown = render_profile_only_report(profile)
    md_path = target / "profile_only.md"
    json_path = target / "profile_only.json"
    md_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "agent_profile": to_dict(profile),
                "observed_performance_score": None,
                "message": NO_OBSERVED_SCORE_MESSAGE,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"markdown": md_path, "json": json_path}


def render_run_report(
    run: FileReadingRun,
    grades: list[FileReadingGrade],
    scorecard: FileReadingScorecard,
    comparison: ComparisonReport | None = None,
    judge_report: FileReadingJudgeReport | None = None,
) -> str:
    lines = [
        "# File Reading Agent Evaluation Report",
        "",
        "## Executive Summary",
        f"- Run id: `{run.run_id}`",
        f"- Status: {run.status}",
        f"- Observed tasks: {len(grades)}",
        f"- Overall observed score: {_score(scorecard.overall_score)}",
        f"- Confidence: {scorecard.confidence}",
        "",
        "## Run Configuration",
        f"- Agent: `{run.agent_profile.agent_id}` - {run.agent_profile.name}",
        f"- Task file: `{_sanitize_path(run.task_file)}`",
        f"- Time budget seconds: {run.time_budget_seconds}",
        f"- Max tasks: {run.max_tasks}",
        f"- Seed: {run.seed}",
        "",
        "## Corpus Summary",
        f"- Corpus id: `{run.corpus_manifest.corpus_id}`",
        f"- Documents: {len(run.corpus_manifest.documents)}",
        f"- Allowed files: {len(run.corpus_manifest.allowed_files)}",
        f"- Forbidden files: {len(run.corpus_manifest.forbidden_files)}",
        f"- Source type: {run.corpus_manifest.source_type}",
        "",
        "## Task Coverage",
        f"- Coverage: {scorecard.coverage}",
    ]
    for task_type, score in sorted(scorecard.task_type_scores.items()):
        lines.append(f"- {task_type}: {score}")
    lines.extend(["", "## Scores By Dimension"])
    lines.extend(f"- {key}: {value}" for key, value in sorted(scorecard.scores_by_dimension.items()))
    lines.extend(
        [
            "",
            "## Scores By Task Type",
        ]
    )
    if scorecard.task_type_scores:
        lines.extend(f"- {key}: {value}" for key, value in sorted(scorecard.task_type_scores.items()))
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Citation Quality",
            f"- Citation score: {scorecard.citation_score}",
            f"- Average span accuracy: {_average(grades, 'citation_span_accuracy')}",
            f"- Average quote match: {_average(grades, 'citation_quote_match')}",
            "",
            "## File Selection Quality",
            f"- Supporting file recall: {_average(grades, 'supporting_file_recall')}",
            f"- Supporting file precision: {_average(grades, 'supporting_file_precision')}",
            "",
            "## Answer Correctness",
            f"- Answer score: {scorecard.answer_score}",
            f"- Exact match count: {sum(1 for grade in grades if grade.answer_exact_match)}",
            "",
            "## Abstention Quality",
            f"- Unanswerable abstention score: {_average(grades, 'unanswerable_abstention_score')}",
            "",
            "## Safety / Forbidden File Results",
            f"- Safety score: {scorecard.safety_score}",
            f"- Forbidden violations: {sum(1 for grade in grades if grade.forbidden_file_violation)}",
            "",
            "## Robustness / Distractor Results",
            f"- Robustness score: {scorecard.robustness_score}",
            f"- Robustness tags observed: {', '.join(sorted({tag for grade in grades for tag in grade.robustness_tags})) or '-'}",
            "",
            "## Efficiency / Timeout",
            f"- Efficiency score: {scorecard.efficiency_score}",
            f"- Timeout count: {sum(1 for trace in run.traces.values() if trace.timeout)}",
            "",
            "## Reference Comparison",
        ]
    )
    if comparison is not None:
        lines.append(f"- Comparable: {comparison.comparable}")
        lines.extend(f"- {item}" for item in comparison.contextual_findings)
        lines.extend(f"- Warning: {item}" for item in comparison.warnings)
    else:
        lines.append("- No reference comparison was provided.")
    lines.extend(["", "## Failure Modes"])
    lines.extend(f"- {item}" for item in scorecard.failure_modes) if scorecard.failure_modes else lines.append("- None observed in this run.")
    lines.extend(["", "## Recommended Changes"])
    grouped_recommendations = prioritized_recommendations_for_grades(
        grades,
        llm_recommendations=_judge_recommendations(judge_report),
    )
    for priority, items in grouped_recommendations.items():
        lines.append(f"- {priority}:")
        lines.extend(f"  - {item}" for item in items)
    lines.extend(["", "## Recommended Next Eval Plan"])
    lines.extend(f"- {item}" for item in scorecard.next_eval_plan)
    lines.extend(["", "## Optional LLM Judge"])
    if judge_report is None:
        lines.append("- Not included. Deterministic grading remains the only score source in this report.")
    else:
        lines.extend(
            [
                f"- Provider: {judge_report.judge_provider}",
                f"- Model: {judge_report.judge_model}",
                f"- Judge based: {judge_report.judge_based}",
                f"- Deterministic: {judge_report.deterministic}",
                f"- Prompt version: {judge_report.prompt_version}",
                f"- Tasks selected: {judge_report.summary.get('tasks_selected', 0)}",
                f"- Calls made: {judge_report.summary.get('calls_made', 0)}",
                f"- Cache hits: {judge_report.summary.get('cache_hits', 0)}",
                f"- Skipped by budget: {judge_report.summary.get('skipped_due_to_budget', 0)}",
                f"- Estimated cost USD: {judge_report.summary.get('estimated_cost_usd', 0)}",
            ]
        )
        failed = [result for result in judge_report.results if result.status == "judge_failed"]
        if failed:
            lines.append(f"- Judge failures: {len(failed)}; deterministic grades were retained for failed judge tasks.")
    lines.extend(
        [
            "",
            "## Limitations",
            "- Scores are deterministic and based only on observed run artifacts.",
            "- Public benchmark references are contextual unless comparable reference results are imported.",
            "- Optional LLM judge scores are non-deterministic supplements and do not replace deterministic scores.",
            "",
            "## Trace Artifact Locations",
        ]
    )
    for task_id, trace in sorted(run.traces.items()):
        lines.append(
            f"- `{task_id}`: stdout `{trace.stdout_path}`, stderr `{trace.stderr_path}`, duration {trace.duration_seconds}s"
        )
    return "\n".join(lines)


def write_run_report(
    run_dir: str | Path,
    *,
    report_format: str = "md,json",
    out_dir: str | Path,
    reference_results: str | Path | None = None,
    include_llm_judge: bool = False,
    judge_report_path: str | Path | None = None,
) -> dict[str, Path]:
    run = load_run(run_dir)
    grades_path = Path(run_dir) / "grades.json"
    if grades_path.exists():
        grades, scorecard = load_grades(grades_path)
        if scorecard is None:
            grades, scorecard = grade_run(run)
    else:
        grades, scorecard = grade_run(run)
    comparison = (
        compare_with_references(run_dir, reference_results)
        if reference_results is not None
        else None
    )
    judge_report = _load_optional_judge_report(
        run_dir,
        include_llm_judge=include_llm_judge,
        judge_report_path=judge_report_path,
    )
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    formats = {item.strip().casefold() for item in report_format.split(",") if item.strip()}
    if "md" in formats or "markdown" in formats:
        md_path = target / "report.md"
        md_path.write_text(
            render_run_report(run, grades, scorecard, comparison, judge_report).rstrip() + "\n",
            encoding="utf-8",
        )
        outputs["markdown"] = md_path
    if "json" in formats:
        json_path = target / "report.json"
        json_path.write_text(
            json.dumps(
                {
                    "run": _sanitized_run_dict(run),
                    "grades": _sanitize_report_value([to_dict(grade) for grade in grades]),
                    "scorecard": _sanitize_report_value(to_dict(scorecard)),
                    "comparison": _sanitize_report_value(to_dict(comparison)) if comparison else None,
                    "llm_judge": _sanitize_report_value(to_dict(judge_report)) if judge_report else None,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        outputs["json"] = json_path
    return outputs


def _score(value: float | None) -> str:
    return "not available" if value is None else str(value)


def _average(grades: list[FileReadingGrade], field: str) -> float:
    values = [float(getattr(grade, field)) for grade in grades]
    return round(sum(values) / len(values), 3) if values else 0.0


def _sanitize_path(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return f"<local>/{candidate.name}"
    return path


def _sanitized_run_dict(run: FileReadingRun) -> dict:
    data = _sanitize_report_value(to_dict(run))
    data["task_file"] = _sanitize_path(str(data.get("task_file", "")))
    manifest = data.get("corpus_manifest")
    if isinstance(manifest, dict):
        manifest["root_path"] = _sanitize_path(str(manifest.get("root_path", "")))
    return data


def _sanitize_report_value(value):
    if isinstance(value, dict):
        return {key: _sanitize_report_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_report_value(item) for item in value]
    if isinstance(value, str):
        candidate = Path(value)
        if candidate.is_absolute():
            return _sanitize_path(value)
        return _sanitize_embedded_paths(value)
    return value


_WINDOWS_PATH_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s`\"'<>|]+")
_POSIX_LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])/(?:Users|home|var|tmp)/[^\s`\"'<>|]+")
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[:=]\s*[^\s,;`'\"<>]+"
)
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


def _sanitize_embedded_paths(value: str) -> str:
    sanitized = _SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=<redacted_secret>", value)
    sanitized = _OPENAI_KEY_RE.sub("<redacted_secret>", sanitized)
    sanitized = _WINDOWS_PATH_RE.sub("<local_path>", sanitized)
    return _POSIX_LOCAL_PATH_RE.sub("<local_path>", sanitized)


def _load_optional_judge_report(
    run_dir: str | Path,
    *,
    include_llm_judge: bool,
    judge_report_path: str | Path | None,
) -> FileReadingJudgeReport | None:
    if not include_llm_judge and judge_report_path is None:
        return None
    candidates = []
    if judge_report_path is not None:
        candidates.append(Path(judge_report_path))
    candidates.append(Path(run_dir) / "llm_judge.json")
    for candidate in candidates:
        if candidate.exists():
            return load_judge_report(candidate)
    return None


def _judge_recommendations(judge_report: FileReadingJudgeReport | None) -> list[str]:
    if judge_report is None:
        return []
    recommendations: list[str] = []
    for result in judge_report.results:
        if result.judge_output is not None:
            recommendations.extend(result.judge_output.recommendation_items)
            if result.judge_output.contradiction_risk >= 0.7:
                recommendations.append(
                    "Review cited evidence and force answer synthesis from quotes only for high contradiction-risk tasks."
                )
    return recommendations
