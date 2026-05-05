from __future__ import annotations

import json
from pathlib import Path

from contract2agent.evaluation.file_reading.graders import load_grades, load_run
from contract2agent.evaluation.file_reading.references import load_reference_results
from contract2agent.evaluation.file_reading.schema import (
    ComparisonReport,
    ReferenceResult,
    to_dict,
)


def compare_with_references(
    run_dir: str | Path,
    reference_results: list[ReferenceResult] | str | Path,
    *,
    out: str | Path | None = None,
) -> ComparisonReport:
    run = load_run(run_dir)
    references = (
        load_reference_results(reference_results)
        if isinstance(reference_results, (str, Path))
        else reference_results
    )
    grades_path = Path(run_dir) / "grades.json"
    scorecard = None
    if grades_path.exists():
        _grades, scorecard = load_grades(grades_path)
    compatible_refs = []
    compatibility_notes: list[str] = []
    contextual_findings: list[str] = []
    warnings = [
        "Reference results are never treated as leaderboard rankings.",
        "Benchmark references remain contextual unless task pack, environment, and scoring method are comparable.",
    ]
    metric_deltas: dict[str, float] = {}
    for reference in references:
        compatible, notes = _compatible(run, reference)
        compatibility_notes.extend(
            f"{reference.reference_result_id}: {note}" for note in notes
        )
        if compatible:
            compatible_refs.append(reference)
        else:
            contextual_findings.append(
                f"{reference.reference_result_id} is contextual only due to incompatible conditions."
            )
    if compatible_refs and scorecard is not None and scorecard.overall_score is not None:
        comparable_metrics = [
            reference.metrics.get("overall_score")
            for reference in compatible_refs
            if "overall_score" in reference.metrics
        ]
        if comparable_metrics:
            metric_deltas["overall_score_vs_reference_mean"] = round(
                scorecard.overall_score - sum(comparable_metrics) / len(comparable_metrics),
                3,
            )
    elif compatible_refs and scorecard is None:
        warnings.append("No local grades.json scorecard was found; metric deltas were not computed.")
    report = ComparisonReport(
        target_run_id=run.run_id,
        reference_results=references,
        comparable=bool(compatible_refs),
        compatibility_notes=compatibility_notes,
        metric_deltas=metric_deltas,
        contextual_findings=contextual_findings,
        warnings=warnings,
        markdown_summary=_markdown_summary(run.run_id, compatible_refs, contextual_findings, metric_deltas, warnings),
    )
    if out is not None:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix.casefold() == ".json":
            target.write_text(json.dumps(to_dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            target.write_text(report.markdown_summary.rstrip() + "\n", encoding="utf-8")
    return report


def _compatible(run: object, reference: ReferenceResult) -> tuple[bool, list[str]]:
    notes: list[str] = []
    compatible = True
    run_task_pack = getattr(run, "metadata", {}).get("task_pack_id", "")
    run_scoring = getattr(run, "metadata", {}).get("scoring_method", "")
    if not reference.comparable_conditions:
        compatible = False
        notes.append("reference comparable_conditions is false")
    if reference.task_pack_id != run_task_pack:
        compatible = False
        notes.append(f"task_pack_id differs ({reference.task_pack_id!r} vs {run_task_pack!r})")
    if reference.scoring_method != run_scoring:
        compatible = False
        notes.append(f"scoring_method differs ({reference.scoring_method!r} vs {run_scoring!r})")
    if not reference.environment:
        compatible = False
        notes.append("reference environment is undocumented")
    if compatible:
        notes.append("task pack, scoring method, and comparable_conditions match")
    return compatible, notes


def _markdown_summary(
    run_id: str,
    compatible_refs: list[ReferenceResult],
    contextual_findings: list[str],
    metric_deltas: dict[str, float],
    warnings: list[str],
) -> str:
    lines = [
        "# File Reading Reference Comparison",
        "",
        f"Target run: `{run_id}`",
        "",
        f"Comparable references: {len(compatible_refs)}",
        "",
        "## Metric Deltas",
    ]
    if metric_deltas:
        lines.extend(f"- `{key}`: {value}" for key, value in sorted(metric_deltas.items()))
    else:
        lines.append("- No metric deltas computed.")
    lines.extend(["", "## Contextual Findings"])
    lines.extend(f"- {item}" for item in contextual_findings) if contextual_findings else lines.append("- None.")
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines)
