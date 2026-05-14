from __future__ import annotations

from collections.abc import Iterable

from contract2agent.evaluation.schema import (
    AgentClassification,
    AgentTypeDefinition,
    EvalCategory,
    EvidenceSource,
)


class AgentTypeRegistry:
    def __init__(self, definitions: Iterable[AgentTypeDefinition]) -> None:
        self._definitions = {definition.type_id: definition for definition in definitions}

    @classmethod
    def default(cls) -> "AgentTypeRegistry":
        return cls(_default_agent_type_definitions())

    def get(self, type_id: str) -> AgentTypeDefinition:
        return self._definitions[type_id]

    def all(self) -> list[AgentTypeDefinition]:
        return [self._definitions[key] for key in sorted(self._definitions)]

    def type_ids(self) -> list[str]:
        return sorted(self._definitions)

    def non_unknown(self) -> list[AgentTypeDefinition]:
        return [
            definition
            for definition in self.all()
            if definition.type_id != "unknown_agent"
        ]


class EvalCategoryRegistry:
    def __init__(self, categories: Iterable[EvalCategory]) -> None:
        self._categories = {
            category.category_id: category for category in categories
        }

    @classmethod
    def default(cls) -> "EvalCategoryRegistry":
        return cls(_default_eval_categories())

    def get(self, category_id: str) -> EvalCategory:
        return self._categories[category_id]

    def all(self) -> list[EvalCategory]:
        return [self._categories[key] for key in sorted(self._categories)]

    def for_agent_type(self, agent_type: str) -> list[EvalCategory]:
        return [
            category
            for category in self.all()
            if agent_type in category.applicable_agent_types
        ]

    def select_for_classification(
        self, classification: AgentClassification
    ) -> list[EvalCategory]:
        selected: dict[str, EvalCategory] = {}
        type_ids = [
            *classification.primary_types,
            *classification.secondary_types,
        ]
        if not type_ids:
            type_ids = ["unknown_agent"]
        if "unknown_agent" in classification.primary_types:
            for category in self.for_agent_type("unknown_agent"):
                selected[category.category_id] = category
        for type_id in type_ids:
            if type_id == "unknown_agent":
                continue
            for category in self.for_agent_type(type_id):
                selected[category.category_id] = category
        return [selected[key] for key in sorted(selected)]


EvalPackRegistry = EvalCategoryRegistry


def default_source_references() -> list[EvidenceSource]:
    return [
        EvidenceSource(
            source_id="openai_agent_evals_methodology",
            source_type="curated_research_reference",
            title="OpenAI agent evaluation methodology",
            url="https://developers.openai.com/api/docs/guides/agent-evals",
            reliability=0.2,
            applies_to=["evaluation_methodology", "workflow_automation_agent", "research_agent"],
            notes=[
                "Context for traces, graders, datasets, and eval runs.",
                "Methodology reference only; not a performance score.",
            ],
            limitations=[
                "No OpenAI eval run is implied for a local agent profile.",
                "Production code does not call external APIs.",
            ],
        ),
        EvidenceSource(
            source_id="reflexion_language_agents_reference",
            source_type="curated_research_reference",
            title="Reflexion: Language Agents with Verbal Reinforcement Learning",
            url="https://arxiv.org/abs/2303.11366",
            reliability=0.2,
            applies_to=["evaluation_methodology"],
            notes=[
                "Context for actor/evaluator/self-reflection loops and episodic verbal memory.",
                "Used to shape global update guidance, not to import a benchmark result.",
            ],
            limitations=[
                "No Reflexion benchmark score is assigned to a local agent profile.",
                "The local update plan is deterministic and does not call an external API.",
            ],
        ),
        EvidenceSource(
            source_id="swe_bench_reference",
            source_type="benchmark_reference",
            title="SWE-bench",
            url="https://www.swebench.com/SWE-bench/guides/evaluation/",
            reliability=0.2,
            applies_to=["coding_agent"],
            notes=[
                "Context for coding-agent evaluation categories involving issue-to-patch tasks and tests.",
                "Failing-to-passing tests are a useful evaluation signal when a comparable run exists.",
            ],
            limitations=[
                "No SWE-bench score is assigned without an actual linked experiment summary.",
                "Leaderboard or model scores are intentionally not embedded.",
            ],
        ),
        EvidenceSource(
            source_id="webarena_reference",
            source_type="benchmark_reference",
            title="WebArena",
            url="https://github.com/web-arena-x/webarena",
            reliability=0.2,
            applies_to=["browser_navigation_agent"],
            notes=[
                "Context for browser-navigation evaluation categories in realistic self-hosted web environments.",
                "Programmatic task validation is useful when a comparable browser run exists.",
            ],
            limitations=[
                "No WebArena score is assigned without an actual linked experiment summary.",
                "The static demo does not fetch live WebArena data.",
            ],
        ),
    ]


def default_benchmark_references() -> list[EvidenceSource]:
    return default_source_references()


def _default_agent_type_definitions() -> list[AgentTypeDefinition]:
    return [
        AgentTypeDefinition(
            type_id="browser_navigation_agent",
            label="Browser Navigation Agent",
            description="Navigates websites, inspects browser state, and may fill or submit forms.",
            capability_signals=["browser", "web navigation", "website", "page", "form"],
            tool_signals=["browser", "navigate", "click", "dom", "screenshot", "form", "submit"],
            task_signals=["navigate", "fill form", "verify page", "gather web", "submit form"],
            negative_signals=["no browser", "offline only"],
            risk_dimensions=["network_access", "external_state", "approval_boundary"],
            applicable_eval_categories=[
                "browser_task_flow",
                "side_effect_and_approval_safety",
                "trace_and_state_observability",
            ],
            evidence_requirements=[
                "controlled browser trace",
                "page-state validation",
                "approval record for submit actions",
            ],
            safety_notes=["Submits and form changes need explicit approval in controlled environments."],
        ),
        AgentTypeDefinition(
            type_id="coding_agent",
            label="Coding Agent",
            description="Reads, edits, or tests repository code and prepares patch-style changes.",
            capability_signals=["code", "repository", "repo", "patch", "test", "build", "diff"],
            tool_signals=["shell", "terminal", "pytest", "git", "file_write", "code_editor", "apply_patch", "compiler", "test_runner"],
            task_signals=["fix failing test", "repair bug", "edit code", "run tests", "build", "minimal diff", "patch"],
            negative_signals=["no code execution", "read only"],
            risk_dimensions=["filesystem_write", "command_execution", "regression_risk"],
            applicable_eval_categories=[
                "coding_change_safety",
                "tool_and_permission_safety",
                "trace_and_state_observability",
            ],
            evidence_requirements=[
                "patch artifact",
                "test or build output",
                "command trace",
            ],
            safety_notes=["Repository changes need workspace containment and test evidence."],
        ),
        AgentTypeDefinition(
            type_id="contract_review_agent",
            label="Contract Review Agent",
            description="Reviews contracts, rules, obligations, clauses, and fact/evidence gaps.",
            capability_signals=["contract", "clause", "obligation", "legal", "rule", "policy"],
            tool_signals=["contract_parser", "clause_extractor", "document_reader", "pdf_reader", "citation"],
            task_signals=["review contract", "identify obligation", "evidence gap", "clause", "fact pattern"],
            negative_signals=["no legal review"],
            risk_dimensions=["grounding", "uncertainty", "advice_boundary"],
            applicable_eval_categories=[
                "document_grounding",
                "evidence_and_citation_quality",
                "trace_and_state_observability",
            ],
            evidence_requirements=[
                "source document",
                "clause-to-output trace",
                "uncertainty handling checks",
            ],
            safety_notes=["Contract output should distinguish workflow review from legal advice."],
        ),
        AgentTypeDefinition(
            type_id="file_reading_agent",
            label="File Reading Agent",
            description="Reads provided files and answers with grounded evidence or citations.",
            capability_signals=["file", "document", "read", "citation", "source", "pdf"],
            tool_signals=["file_read", "reader", "pdf_reader", "document_reader", "citation", "search_local"],
            task_signals=["cite source", "answer from files", "summarize document", "missing file", "quote evidence"],
            negative_signals=["no file access"],
            risk_dimensions=["private_data", "grounding", "missing_file_handling"],
            applicable_eval_categories=[
                "document_grounding",
                "evidence_and_citation_quality",
                "tool_and_permission_safety",
            ],
            evidence_requirements=[
                "provided file corpus",
                "answer-to-source trace",
                "missing-file behavior test",
            ],
            safety_notes=["Read access is not proof of grounded answers."],
        ),
        AgentTypeDefinition(
            type_id="financial_transaction_agent_simulated",
            label="Financial Transaction Agent (Simulated)",
            description="Handles simulated-only payment, ordering, trading, or transfer workflows.",
            capability_signals=["payment", "transaction", "trade", "order", "checkout", "transfer"],
            tool_signals=["payment", "transfer", "trade", "order", "checkout", "bank", "card", "transaction"],
            task_signals=["authorize payment", "confirm transfer", "place order", "simulate trade", "audit trail", "refuse unsafe"],
            negative_signals=["real funds prohibited", "simulation only"],
            risk_dimensions=["financial_side_effect", "authorization", "auditability", "approval_boundary"],
            applicable_eval_categories=[
                "simulated_transaction_safety",
                "side_effect_and_approval_safety",
                "trace_and_state_observability",
            ],
            simulation_only=True,
            evidence_requirements=[
                "simulation sandbox",
                "approval trace",
                "refusal tests for unsafe transaction requests",
            ],
            safety_notes=[
                "Real financial transactions are out of scope.",
                "Simulated financial workflows are high risk by default.",
            ],
        ),
        AgentTypeDefinition(
            type_id="general_tool_use_agent",
            label="General Tool-Use Agent",
            description="Uses tools but does not fit a more specific broad family from supplied evidence.",
            capability_signals=["tool", "api", "action", "assistant"],
            tool_signals=["tool", "api", "connector", "integration", "function"],
            task_signals=["use tool", "call api", "complete task", "take action"],
            negative_signals=[],
            risk_dimensions=["tool_permissions", "state_change", "approval_boundary"],
            applicable_eval_categories=[
                "tool_and_permission_safety",
                "trace_and_state_observability",
            ],
            evidence_requirements=[
                "tool inventory",
                "sample task trace",
                "permission boundary description",
            ],
        ),
        AgentTypeDefinition(
            type_id="research_agent",
            label="Research Agent",
            description="Finds, evaluates, and synthesizes sources with uncertainty handling.",
            capability_signals=["research", "source", "citation", "evidence", "freshness", "paper"],
            tool_signals=["web_search", "search", "browser", "reader", "citation", "scholar"],
            task_signals=["find sources", "synthesize evidence", "conflicting evidence", "cite", "freshness"],
            negative_signals=["no web", "no research"],
            risk_dimensions=["source_quality", "freshness", "citation_grounding"],
            applicable_eval_categories=[
                "research_source_quality",
                "evidence_and_citation_quality",
                "trace_and_state_observability",
            ],
            evidence_requirements=[
                "source list",
                "citation-to-claim trace",
                "conflicting-evidence task",
            ],
        ),
        AgentTypeDefinition(
            type_id="workflow_automation_agent",
            label="Workflow Automation Agent",
            description="Coordinates multi-step tool workflows, routing, handoff, and state.",
            capability_signals=["workflow", "automation", "handoff", "routing", "state", "orchestration"],
            tool_signals=["scheduler", "queue", "router", "email", "calendar", "workflow", "handoff"],
            task_signals=["multi-step", "handoff", "route", "state tracking", "loop control", "approval workflow"],
            negative_signals=[],
            risk_dimensions=["state_management", "loop_control", "handoff_correctness"],
            applicable_eval_categories=[
                "workflow_state_control",
                "side_effect_and_approval_safety",
                "trace_and_state_observability",
            ],
            evidence_requirements=[
                "multi-step trace",
                "state transition record",
                "loop and handoff boundary tests",
            ],
        ),
        AgentTypeDefinition(
            type_id="unknown_agent",
            label="Unknown or Partially Specified Agent",
            description="Fallback when supplied evidence is too sparse for a concrete family.",
            capability_signals=[],
            tool_signals=[],
            task_signals=[],
            negative_signals=[],
            risk_dimensions=["missing_evidence", "unknown_permissions"],
            applicable_eval_categories=["profile_completion"],
            evidence_requirements=[
                "tool inventory",
                "sample tasks",
                "permission boundaries",
                "experiment or trace summary",
            ],
            safety_notes=["Unknown is preferred over unsupported positive claims."],
        ),
    ]


def _default_eval_categories() -> list[EvalCategory]:
    return [
        EvalCategory(
            category_id="browser_task_flow",
            label="Browser Task Flow",
            applicable_agent_types=["browser_navigation_agent"],
            what_it_tests=["navigation intent", "page-state verification", "form interaction boundaries"],
            required_evidence=["controlled browser trace", "state validation artifact"],
            example_tasks=["Navigate a controlled site and verify the requested state without unapproved submit."],
            scoring_dimensions=["capability_fit", "tool_risk", "task_clarity"],
            known_benchmark_references=["webarena_reference"],
            limitations=["This category does not run WebArena or assign benchmark scores."],
        ),
        EvalCategory(
            category_id="coding_change_safety",
            label="Coding Change Safety",
            applicable_agent_types=["coding_agent"],
            what_it_tests=["patch relevance", "test evidence", "command discipline"],
            required_evidence=["patch artifact", "test/build output", "command trace"],
            example_tasks=["Apply a minimal repository patch and report observed test output."],
            scoring_dimensions=["capability_fit", "evidence_strength", "expected_reliability"],
            known_benchmark_references=["swe_bench_reference"],
            limitations=["This category is not a SWE-bench runner."],
        ),
        EvalCategory(
            category_id="document_grounding",
            label="Document Grounding",
            applicable_agent_types=["file_reading_agent", "contract_review_agent"],
            what_it_tests=["answer grounding", "missing-file behavior", "source boundary discipline"],
            required_evidence=["source document", "answer-to-source trace"],
            example_tasks=["Answer a question from provided files and identify missing evidence."],
            scoring_dimensions=["capability_fit", "evidence_strength", "data_access_risk"],
            known_benchmark_references=[],
            limitations=["Grounding quality requires observed answer/source artifacts."],
        ),
        EvalCategory(
            category_id="evidence_and_citation_quality",
            label="Evidence And Citation Quality",
            applicable_agent_types=["file_reading_agent", "contract_review_agent", "research_agent"],
            what_it_tests=["citation support", "uncertainty handling", "claim-to-source traceability"],
            required_evidence=["cited output", "source list", "grader notes"],
            example_tasks=["Produce a cited answer and mark unsupported claims as unknown."],
            scoring_dimensions=["evidence_strength", "task_clarity", "expected_reliability"],
            known_benchmark_references=["openai_agent_evals_methodology"],
            limitations=["Citations are not judged without supplied source artifacts."],
        ),
        EvalCategory(
            category_id="profile_completion",
            label="Profile Completion",
            applicable_agent_types=["unknown_agent"],
            what_it_tests=["tool inventory completeness", "permission clarity", "sample task specificity"],
            required_evidence=["agent description", "tools", "sample tasks", "constraints"],
            example_tasks=["Complete the profile before making performance claims."],
            scoring_dimensions=["missing_evidence_penalty", "task_clarity"],
            known_benchmark_references=[],
            limitations=["No performance score is available for sparse profiles."],
        ),
        EvalCategory(
            category_id="research_source_quality",
            label="Research Source Quality",
            applicable_agent_types=["research_agent"],
            what_it_tests=["source selection", "freshness awareness", "conflicting evidence handling"],
            required_evidence=["source list", "citation trace", "timestamped claims when freshness matters"],
            example_tasks=["Find primary sources and explain uncertainty around conflicting claims."],
            scoring_dimensions=["evidence_strength", "task_clarity", "expected_reliability"],
            known_benchmark_references=["openai_agent_evals_methodology"],
            limitations=["This category does not fetch or grade live web results."],
        ),
        EvalCategory(
            category_id="side_effect_and_approval_safety",
            label="Side Effect And Approval Safety",
            applicable_agent_types=[
                "browser_navigation_agent",
                "financial_transaction_agent_simulated",
                "workflow_automation_agent",
            ],
            what_it_tests=["approval gates", "external-state modification control", "refusal behavior"],
            required_evidence=["approval trace", "negative unsafe-action tests"],
            example_tasks=["Attempt a side-effect action and verify the agent asks for approval or refuses."],
            scoring_dimensions=["approval_safety", "tool_risk", "autonomy_risk"],
            known_benchmark_references=[],
            limitations=["Real external actions are out of scope."],
        ),
        EvalCategory(
            category_id="simulated_transaction_safety",
            label="Simulated Transaction Safety",
            applicable_agent_types=["financial_transaction_agent_simulated"],
            what_it_tests=["authorization", "confirmation", "auditability", "unsafe request refusal"],
            required_evidence=["simulation-only tool surface", "approval trace", "audit log"],
            example_tasks=["Refuse an unapproved simulated transfer and record the missing approval."],
            scoring_dimensions=["approval_safety", "tool_risk", "expected_reliability"],
            known_benchmark_references=[],
            limitations=["Financial transaction evaluation is simulation-only."],
        ),
        EvalCategory(
            category_id="tool_and_permission_safety",
            label="Tool And Permission Safety",
            applicable_agent_types=["coding_agent", "file_reading_agent", "general_tool_use_agent"],
            what_it_tests=["permission boundaries", "private data access", "tool selection rationale"],
            required_evidence=["tool inventory", "permission model", "negative boundary tests"],
            example_tasks=["Verify the agent refuses actions outside declared permissions."],
            scoring_dimensions=["tool_risk", "data_access_risk", "approval_safety"],
            known_benchmark_references=[],
            limitations=["Permission safety does not prove task competence."],
        ),
        EvalCategory(
            category_id="trace_and_state_observability",
            label="Trace And State Observability",
            applicable_agent_types=[
                "browser_navigation_agent",
                "coding_agent",
                "contract_review_agent",
                "financial_transaction_agent_simulated",
                "general_tool_use_agent",
                "research_agent",
                "workflow_automation_agent",
            ],
            what_it_tests=["trace availability", "artifact capture", "state transition evidence"],
            required_evidence=["trace summary", "artifacts", "verdict or grader notes"],
            example_tasks=["Record tool calls, state changes, final output, and evidence for review."],
            scoring_dimensions=["evidence_strength", "missing_evidence_penalty"],
            known_benchmark_references=["openai_agent_evals_methodology"],
            limitations=["Trace availability improves confidence but does not by itself prove correctness."],
        ),
        EvalCategory(
            category_id="workflow_state_control",
            label="Workflow State Control",
            applicable_agent_types=["workflow_automation_agent"],
            what_it_tests=["state persistence", "handoff correctness", "loop control"],
            required_evidence=["multi-step trace", "state transition log"],
            example_tasks=["Complete a routed workflow with bounded retries and explicit handoff state."],
            scoring_dimensions=["autonomy_risk", "task_clarity", "expected_reliability"],
            known_benchmark_references=["openai_agent_evals_methodology"],
            limitations=["This category is a broad eval category, not a specialized workflow scorer."],
        ),
    ]
