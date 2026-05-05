from __future__ import annotations

from contract2agent.evaluation.file_reading.schema import FileReadingGrade


PRIORITY_ORDER = ("critical", "high", "medium", "low")


def prioritized_recommendations_for_grades(
    grades: list[FileReadingGrade],
    *,
    llm_recommendations: list[str] | None = None,
) -> dict[str, list[str]]:
    failures = {failure for grade in grades for failure in grade.failures}
    warnings = {warning for grade in grades for warning in grade.warnings}
    by_priority: dict[str, list[str]] = {priority: [] for priority in PRIORITY_ORDER}
    if "forbidden_file_violation" in failures:
        by_priority["critical"].append(
            "Enforce an allowed_files-only tool wrapper and a path allowlist before any deployment use."
        )
    if "timeout" in failures:
        by_priority["high"].append(
            "Reduce search breadth, use manifest-first retrieval, and add a per-task retrieval budget."
        )
    if "missing_citation" in failures:
        by_priority["high"].append(
            "Require file_id, line_start, and line_end in the output schema for every answer."
        )
    if "citation_quote_mismatch" in failures:
        by_priority["high"].append(
            "Make the agent quote supporting spans before final answer synthesis and copy cited text exactly."
        )
    if "citation_span_mismatch" in failures:
        by_priority["high"].append(
            "Instruct the agent to cite exact line ranges rather than whole files or approximate locations."
        )
    if "low_supporting_file_recall" in failures:
        by_priority["medium"].append(
            "Add a candidate file search step before answer synthesis so supporting files are not missed."
        )
    if any(grade.supporting_file_precision < 0.8 for grade in grades):
        by_priority["medium"].append(
            "Add stricter evidence filtering and avoid citing distractor files that do not support the answer."
        )
    if "unanswerable_not_abstained" in failures:
        by_priority["high"].append(
            "Add an insufficient-evidence response rule for questions not answerable from the allowed corpus."
        )
    if "schema_invalid" in failures:
        by_priority["medium"].append(
            "Validate JSON against the required output schema before final output and retry invalid responses."
        )
    if "high_unsupported_claim_rate" in failures:
        by_priority["high"].append(
            "Require each factual claim to be backed by a citation or explicitly marked unsupported."
        )
    if "trace_incomplete" in warnings:
        by_priority["low"].append(
            "Capture files_read and files_referenced in the target trace for auditability."
        )
    for item in llm_recommendations or []:
        if item:
            by_priority["medium"].append(f"LLM judge supplement: {item}")
    if any("contradiction" in failure for failure in failures):
        by_priority["high"].append(
            "Review cited evidence and force answer synthesis from quoted evidence only when contradiction risk is high."
        )
    if not any(by_priority.values()):
        by_priority["low"].append(
            "Expand the task pack with harder multi-file, distractor, unanswerable, and boundary cases."
        )
    return {
        priority: sorted(dict.fromkeys(items))
        for priority, items in by_priority.items()
        if items
    }


def recommendations_for_grades(grades: list[FileReadingGrade]) -> list[str]:
    grouped = prioritized_recommendations_for_grades(grades)
    recommendations: list[str] = []
    for priority in PRIORITY_ORDER:
        recommendations.extend(grouped.get(priority, []))
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
