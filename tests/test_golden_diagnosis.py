from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from contract2agent.counterexamples import generate_counterexamples
from contract2agent.diagnosis import diagnose_evaluation
from contract2agent.diagnosis_schema import DiagnosisIssue
from contract2agent.parser import parse_requirement


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "fixtures" / "golden"


def test_missing_file_expected_golden() -> None:
    expected = _golden("missing_file_expected.json")
    contract = parse_requirement("Read a PDF paper and produce notes.")
    report = diagnose_evaluation(
        contract,
        [{"case": "write_after_missing_file", "passed": True}],
        {"write_after_missing_file": _missing_file_then_write_trace()},
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

    _assert_first_issue_matches_golden(report.issues, expected)


def test_forbidden_tool_expected_golden() -> None:
    expected = _golden("forbidden_tool_expected.json")
    contract = parse_requirement("Build a paper reader agent with no web search.")
    trace = [
        {"type": "tool_call", "tool": "web_search", "args": {"query": "paper"}},
        {"type": "tool_result", "tool": "web_search", "result": {"status": "ok"}},
    ]

    report = diagnose_evaluation(
        contract,
        [{"case": "forbidden_web_search", "passed": True}],
        {"forbidden_web_search": trace},
    )

    _assert_first_issue_matches_golden(report.issues, expected)


def test_valid_trace_rejected_expected_golden() -> None:
    expected = _golden("valid_trace_rejected_expected.json")
    contract = parse_requirement(
        "Read a PDF paper, handle file not found, and do not browse the web."
    )
    trace = _counterexample_trace(contract, "valid_read_then_write")

    report = diagnose_evaluation(
        contract,
        [
            {
                "case": "valid_read_then_write",
                "passed": False,
                "rule": "must_read_before_write",
                "message": "markdown_writer was rejected.",
            }
        ],
        {"valid_read_then_write": trace},
        manifest={
            "cases": [
                {"name": "valid_read_then_write", "expected_to_fail": False}
            ]
        },
    )

    _assert_first_issue_matches_golden(report.issues, expected)


def test_service_payment_static_sample_matches_golden_fixture() -> None:
    expected = _golden("service_payment_expected.json")
    sample = json.loads((ROOT / expected["sample_path"]).read_text(encoding="utf-8"))
    combined_text = " ".join(
        [
            sample["contract_text"],
            sample["dispute_description"],
            sample["claimant_position"],
            sample["respondent_position"],
        ]
    )

    assert sample["name"] == expected["name"]
    assert sample["contract_type"] == expected["contract_type"]
    assert sample["dispute_type"] == expected["dispute_type"]
    assert sample["configuration"] == expected["configuration"]
    for evidence in expected["must_include_evidence"]:
        assert evidence in sample["evidence"]
    for phrase in expected["text_contains"]:
        assert phrase in combined_text


def _assert_first_issue_matches_golden(
    issues: list[DiagnosisIssue],
    expected: dict[str, Any],
) -> None:
    assert [issue.id for issue in issues] == [
        f"ATD{index:03d}" for index in range(1, len(issues) + 1)
    ]
    issue = issues[0]
    assert issue.id == expected["id"]
    assert issue.category == expected["category"]
    assert issue.strictness == expected["strictness"]
    assert issue.affected_agent_part == expected["affected_agent_part"]
    for phrase in expected["cause_contains"]:
        assert phrase in issue.natural_language_cause
    assert issue.suggested_patch
    assert issue.suggested_patch["type"] == expected["suggested_patch_type"]
    assert issue.suggested_regression_trace
    assert _tools_in(issue.suggested_regression_trace) == expected["suggested_regression_tools"]
    json.dumps(issue.to_dict())


def _tools_in(trace: list[dict[str, Any]]) -> list[str]:
    tools: list[str] = []
    for event in trace:
        tool = event.get("tool")
        if isinstance(tool, str) and tool not in tools:
            tools.append(tool)
    return tools


def _counterexample_trace(contract: Any, name: str) -> list[dict[str, Any]]:
    for case in generate_counterexamples(contract):
        if case.name == name:
            return case.trace
    raise AssertionError(f"Missing counterexample: {name}")


def _missing_file_then_write_trace() -> list[dict[str, Any]]:
    return [
        {"type": "tool_call", "tool": "pdf_reader", "args": {"path": "missing.pdf"}},
        {
            "type": "tool_result",
            "tool": "pdf_reader",
            "result": {"status": "file_not_found"},
        },
        {"type": "tool_call", "tool": "markdown_writer", "args": {"path": "notes.md"}},
        {"type": "tool_result", "tool": "markdown_writer", "result": {"status": "ok"}},
    ]


def _golden(filename: str) -> dict[str, Any]:
    return json.loads((GOLDEN / filename).read_text(encoding="utf-8"))
