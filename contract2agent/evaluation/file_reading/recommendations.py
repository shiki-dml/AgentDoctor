from __future__ import annotations

from contract2agent.evaluation.file_reading.schema import FileReadingGrade


def recommendations_for_grades(grades: list[FileReadingGrade]) -> list[str]:
    failures = {failure for grade in grades for failure in grade.failures}
    warnings = {warning for grade in grades for warning in grade.warnings}
    recommendations: list[str] = []
    if "missing_citation" in failures:
        recommendations.append("Require output citations with file_id plus line_start/line_end for every answer.")
    if "citation_quote_mismatch" in failures:
        recommendations.append("Quote supporting spans before final answer synthesis and copy cited text exactly.")
    if "forbidden_file_violation" in failures:
        recommendations.append("Add an allowed_files-only instruction and enforce a tool-level path allowlist.")
    if "unanswerable_not_abstained" in failures:
        recommendations.append("Add an explicit insufficient-evidence response rule for unanswerable questions.")
    if "low_supporting_file_recall" in failures:
        recommendations.append("List candidate files from the manifest before answer synthesis on multi-file tasks.")
    if "schema_invalid" in failures:
        recommendations.append("Validate the target output JSON schema before returning the final answer.")
    if "timeout" in failures:
        recommendations.append("Reduce search breadth or add manifest-first retrieval to stay within task budgets.")
    if "high_unsupported_claim_rate" in failures:
        recommendations.append("Require every factual claim to be linked to a cited source span or marked unsupported.")
    if "trace_incomplete" in warnings:
        recommendations.append("Capture files_read and files_referenced in the target trace for auditability.")
    if not recommendations:
        recommendations.append("Expand the task pack with harder multi-file, distractor, and boundary cases.")
    return sorted(dict.fromkeys(recommendations))


def next_eval_plan_for_grades(grades: list[FileReadingGrade]) -> list[str]:
    plan = [
        "Run a larger deterministic task pack with single-file, multi-file, unanswerable, and boundary cases.",
        "Keep benchmark references contextual unless comparable run artifacts are imported.",
    ]
    if any("low_supporting_file_recall" in grade.failures for grade in grades):
        plan.append("Add multi-hop tasks that require evidence from two or more files.")
    if any("forbidden_file_violation" in grade.failures for grade in grades):
        plan.append("Add more forbidden-file and path-containment tasks before deployment.")
    if any("timeout" in grade.failures for grade in grades):
        plan.append("Run a budget sweep with smaller and larger time limits to identify retrieval bottlenecks.")
    return sorted(dict.fromkeys(plan))
