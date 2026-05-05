from __future__ import annotations

import json
from pathlib import Path

from contract2agent.evaluation.file_reading.compare import compare_with_references
from contract2agent.evaluation.file_reading.graders import grade_run, load_grades, load_run
from contract2agent.evaluation.file_reading.runner import load_file_reading_agent_profile
from contract2agent.evaluation.file_reading.schema import (
    ComparisonReport,
    FileReadingAgentProfile,
    FileReadingGrade,
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
    lines.extend(f"- {item}" for item in scorecard.recommended_changes)
    lines.extend(["", "## Recommended Next Eval Plan"])
    lines.extend(f"- {item}" for item in scorecard.next_eval_plan)
    lines.extend(
        [
            "",
            "## Limitations",
            "- Scores are deterministic and based only on observed run artifacts.",
            "- Public benchmark references are contextual unless comparable reference results are imported.",
            "- Optional semantic or LLM judging is not enabled in this core adapter.",
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
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    formats = {item.strip().casefold() for item in report_format.split(",") if item.strip()}
    if "md" in formats or "markdown" in formats:
        md_path = target / "report.md"
        md_path.write_text(
            render_run_report(run, grades, scorecard, comparison).rstrip() + "\n",
            encoding="utf-8",
        )
        outputs["markdown"] = md_path
    if "json" in formats:
        json_path = target / "report.json"
        json_path.write_text(
            json.dumps(
                {
                    "run": to_dict(run),
                    "grades": [to_dict(grade) for grade in grades],
                    "scorecard": to_dict(scorecard),
                    "comparison": to_dict(comparison) if comparison else None,
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
