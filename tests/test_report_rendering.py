from __future__ import annotations

import json
import re
from pathlib import Path

from contract2agent.diagnosis import diagnose_evaluation, write_diagnosis_report_markdown
from contract2agent.parser import parse_requirement


def test_markdown_report_has_required_sections_without_artifacts(
    contract2agent_test_root: Path,
) -> None:
    report = _diagnosis_report()
    report_path = contract2agent_test_root / "report_rendering" / "diagnosis.md"

    write_diagnosis_report_markdown(report, report_path)
    markdown = report_path.read_text(encoding="utf-8")

    for required in (
        "# Diagnosis Report",
        "## Executive Summary",
        "## Issue Counts by Category",
        "## Issue Counts by Affected Agent Part",
        "## Rule Coverage Matrix",
        "## Issues",
        "ATD001",
        "- Category:",
        "- Strictness:",
        "- Affected agent part:",
        "Cause:",
        "- Evidence:",
        "Suggested fix:",
        "#### Suggested Patch",
        "#### Suggested Regression Trace",
    ):
        assert required in markdown

    assert "DiagnosisIssue(" not in markdown
    assert "object at 0x" not in markdown
    assert "None" not in markdown
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", markdown)


def test_report_dict_is_json_serializable_with_structured_fields() -> None:
    report = _diagnosis_report()
    data = json.loads(json.dumps(report.to_dict()))

    assert data["total_issues"] == len(data["issues"])
    assert data["issue_counts_by_category"]
    assert data["issue_counts_by_affected_part"]
    assert data["issues"]
    assert isinstance(data["issues"][0]["category"], str)
    assert isinstance(data["issues"][0]["strictness"], str)
    assert isinstance(data["issues"][0]["evidence"], dict)
    assert isinstance(data["issues"][0]["suggested_patch"], dict)
    assert isinstance(data["issues"][0]["suggested_regression_trace"], list)
    assert "rule_coverage" in data
    assert isinstance(data["rule_coverage"], list)


def _diagnosis_report():
    contract = parse_requirement("Read a PDF paper and produce notes.")
    trace = [
        {"type": "tool_call", "tool": "pdf_reader", "args": {"path": "missing.pdf"}},
        {
            "type": "tool_result",
            "tool": "pdf_reader",
            "result": {"status": "file_not_found"},
        },
        {"type": "tool_call", "tool": "markdown_writer", "args": {"path": "notes.md"}},
        {"type": "tool_result", "tool": "markdown_writer", "result": {"status": "ok"}},
    ]
    return diagnose_evaluation(
        contract,
        [{"case": "write_after_missing_file", "passed": True}],
        {"write_after_missing_file": trace},
        manifest={
            "cases": [
                {
                    "name": "write_after_missing_file",
                    "expected_to_fail": True,
                    "expected_rule": "no_write_on_missing_file",
                }
            ]
        },
    )
