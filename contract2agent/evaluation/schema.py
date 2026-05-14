from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]


EVIDENCE_SOURCE_TYPES = {
    "user_declared",
    "inferred_from_tools",
    "inferred_from_tasks",
    "observed_experiment",
    "imported_trace",
    "benchmark_reference",
    "curated_research_reference",
    "synthetic_sample",
    "missing",
}


@dataclass
class ToolSurface:
    name: str
    category: str = "unspecified"
    mode: str = "unknown"
    scope: str = "unknown"
    side_effect_level: str = "none"
    requires_approval: bool = False
    can_modify_state: bool = False
    can_access_private_data: bool = False
    risk_tags: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    can_modify_external_state: bool = False

    def modifies_state(self) -> bool:
        return self.can_modify_state or self.can_modify_external_state


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    description: str = ""
    declared_capabilities: list[str] = field(default_factory=list)
    tools: list[ToolSurface] = field(default_factory=list)
    tool_permissions: list[str] = field(default_factory=list)
    data_access: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    autonomy_level: str = "unknown"
    requires_human_approval: bool = False
    can_read_files: bool = False
    can_write_files: bool = False
    can_run_code: bool = False
    can_use_browser: bool = False
    can_use_network: bool = False
    can_execute_transactions: bool = False
    can_modify_external_state: bool = False
    sample_tasks: list[str] = field(default_factory=list)
    policy_constraints: list[str] = field(default_factory=list)
    environment: str = "unspecified"
    metadata: JsonObject = field(default_factory=dict)


@dataclass
class CapabilitySignal:
    signal_id: str
    label: str
    source_field: str
    matched_value: str
    capability: str
    strength: str
    confidence: float
    explanation: str


@dataclass
class AgentTypeDefinition:
    type_id: str
    label: str
    description: str
    capability_signals: list[str] = field(default_factory=list)
    tool_signals: list[str] = field(default_factory=list)
    task_signals: list[str] = field(default_factory=list)
    negative_signals: list[str] = field(default_factory=list)
    risk_dimensions: list[str] = field(default_factory=list)
    applicable_eval_categories: list[str] = field(default_factory=list)
    simulation_only: bool = False
    default_confidence: float = 0.0
    evidence_requirements: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)


@dataclass
class AgentClassification:
    primary_types: list[str] = field(default_factory=list)
    secondary_types: list[str] = field(default_factory=list)
    rejected_types: list[str] = field(default_factory=list)
    confidence_by_type: dict[str, float] = field(default_factory=dict)
    matched_signals: dict[str, list[CapabilitySignal]] = field(default_factory=dict)
    negative_signals: dict[str, list[CapabilitySignal]] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class EvalCategory:
    category_id: str
    label: str
    applicable_agent_types: list[str] = field(default_factory=list)
    what_it_tests: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    example_tasks: list[str] = field(default_factory=list)
    scoring_dimensions: list[str] = field(default_factory=list)
    known_benchmark_references: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class EvidenceSource:
    source_id: str
    source_type: str
    title: str
    url: str = ""
    local_path: str = ""
    reliability: float = 0.0
    applies_to: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ExperimentSummary:
    result_id: str
    agent_id: str
    agent_type: str
    eval_category: str
    task_summary: str
    metrics: dict[str, float] = field(default_factory=dict)
    verdict: str = "unknown"
    evidence_source: str = "missing"
    trace_available: bool = False
    limitations: list[str] = field(default_factory=list)
    environment: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    failure_modes: list[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class PreliminaryScore:
    dimension: str
    score: float
    confidence: float
    evidence_sources: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class OutcomePrediction:
    predicted_success: float | None = None
    confidence: float = 0.0
    likely_strengths: list[str] = field(default_factory=list)
    likely_failures: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    evidence_basis: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    recommended_next_tests: list[str] = field(default_factory=list)
    explanation: str = ""
    target_context: str = "general target workflow"

    @property
    def likely_success(self) -> float | None:
        return self.predicted_success


@dataclass
class ReflexionUpdate:
    update_id: str
    trigger: str
    reflection: str
    next_instruction: str
    priority: str = "medium"
    scope: str = "global_agent_behavior"
    evidence_sources: list[str] = field(default_factory=list)
    applies_to: list[str] = field(default_factory=list)


@dataclass
class ReflexionUpdatePlan:
    strategy: str = "verbal_reinforcement"
    api_required: bool = False
    actor: str = "agent_under_evaluation"
    evaluator: str = "contract2agent_evidence_pipeline"
    reflector: str = "deterministic_reflexion_update_builder"
    summary: str = ""
    memory: list[ReflexionUpdate] = field(default_factory=list)
    next_agent_context: list[str] = field(default_factory=list)
    api_key_policy: str = ""
    source_references: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class EvidenceBundle:
    agent_id: str
    classification: AgentClassification
    applicable_eval_categories: list[EvalCategory] = field(default_factory=list)
    experiment_summaries: list[ExperimentSummary] = field(default_factory=list)
    data_sources: list[EvidenceSource] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    evidence_quality_score: float = 0.0
    coverage_by_type: dict[str, float] = field(default_factory=dict)

    @property
    def applicable_eval_packs(self) -> list[EvalCategory]:
        return self.applicable_eval_categories

    @property
    def experiment_results(self) -> list[ExperimentSummary]:
        return self.experiment_summaries

    @property
    def benchmark_references(self) -> list[EvidenceSource]:
        return [
            source
            for source in self.data_sources
            if source.source_type in {"benchmark_reference", "curated_research_reference"}
        ]


@dataclass
class AgentScorecard:
    agent_id: str
    preliminary_scores: list[PreliminaryScore] = field(default_factory=list)
    overall_score: float | None = None
    confidence: float = 0.0
    coverage: float = 0.0
    scores_by_dimension: dict[str, float] = field(default_factory=dict)
    scores_by_type: dict[str, float] = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    recommended_next_evals: list[str] = field(default_factory=list)
    prediction_summary: str = ""


@dataclass
class AgentEvaluationReport:
    agent_profile: AgentProfile
    classification: AgentClassification
    inferred_capabilities: list[str]
    applicable_eval_categories: list[EvalCategory]
    evidence_summary: list[EvidenceSource]
    preliminary_scores: list[PreliminaryScore]
    outcome_prediction: OutcomePrediction
    reflexion_update_plan: ReflexionUpdatePlan
    data_sources: list[EvidenceSource]
    missing_evidence: list[str]
    limitations: list[str]
    report_markdown: str
    report_json: JsonObject


CapabilityClassification = AgentClassification
EvalPackSummary = EvalCategory
EvalPack = EvalCategory
ExperimentResult = ExperimentSummary
BenchmarkReference = EvidenceSource


def to_dict(value: Any) -> Any:
    """Return a JSON-serializable structure for dataclasses and nested values."""
    if is_dataclass(value):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dict(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def agent_profile_from_dict(data: JsonObject) -> AgentProfile:
    profile_data = dict(data)
    profile_data["tools"] = [
        tool_surface_from_dict(tool) for tool in profile_data.get("tools", [])
    ]
    return AgentProfile(**_filter_kwargs(AgentProfile, profile_data))


def tool_surface_from_dict(data: str | JsonObject) -> ToolSurface:
    if isinstance(data, str):
        return ToolSurface(name=data)
    tool_data = dict(data)
    if "can_modify_external_state" in tool_data and "can_modify_state" not in tool_data:
        tool_data["can_modify_state"] = bool(tool_data["can_modify_external_state"])
    return ToolSurface(**_filter_kwargs(ToolSurface, tool_data))


def eval_category_from_dict(data: JsonObject) -> EvalCategory:
    category_data = dict(data)
    if "pack_id" in category_data and "category_id" not in category_data:
        category_data["category_id"] = category_data["pack_id"]
    if "agent_type" in category_data and "applicable_agent_types" not in category_data:
        category_data["applicable_agent_types"] = [category_data["agent_type"]]
    return EvalCategory(**_filter_kwargs(EvalCategory, category_data))


def eval_pack_from_dict(data: JsonObject) -> EvalCategory:
    return eval_category_from_dict(data)


def evidence_source_from_dict(data: JsonObject) -> EvidenceSource:
    source_data = dict(data)
    if "reference_id" in source_data and "source_id" not in source_data:
        source_data["source_id"] = source_data["reference_id"]
    if "source_url" in source_data and "url" not in source_data:
        source_data["url"] = source_data["source_url"]
    if "domain" in source_data and "applies_to" not in source_data:
        source_data["applies_to"] = [source_data["domain"]]
    if "source_type" not in source_data:
        source_data["source_type"] = "curated_research_reference"
    if source_data["source_type"] not in EVIDENCE_SOURCE_TYPES:
        source_data["source_type"] = "curated_research_reference"
    if "reliability" not in source_data:
        source_data["reliability"] = _default_reliability(source_data["source_type"])
    return EvidenceSource(**_filter_kwargs(EvidenceSource, source_data))


def experiment_summary_from_dict(data: JsonObject) -> ExperimentSummary:
    result_data = dict(data)
    if "run_id" in result_data and "result_id" not in result_data:
        result_data["result_id"] = result_data["run_id"]
    if "eval_pack_id" in result_data and "eval_category" not in result_data:
        result_data["eval_category"] = result_data["eval_pack_id"]
    if "task_summary" not in result_data:
        result_data["task_summary"] = str(
            result_data.get("task_id")
            or result_data.get("trace_summary", {}).get("final_output")
            or "Experiment summary"
        )
    if "trace_available" not in result_data:
        result_data["trace_available"] = bool(result_data.get("trace_summary"))
    if "evidence_source" not in result_data:
        result_data["evidence_source"] = "observed_experiment"
    if result_data["evidence_source"] == "observed_run":
        result_data["evidence_source"] = "observed_experiment"
    return ExperimentSummary(**_filter_kwargs(ExperimentSummary, result_data))


def experiment_result_from_dict(data: JsonObject) -> ExperimentSummary:
    return experiment_summary_from_dict(data)


def benchmark_reference_from_dict(data: JsonObject) -> EvidenceSource:
    return evidence_source_from_dict(data)


def load_agent_profile(path: str | Path) -> AgentProfile:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Agent profile JSON must contain an object: {path}")
    return agent_profile_from_dict(data)


def _filter_kwargs(cls: type, data: JsonObject) -> JsonObject:
    field_names = set(getattr(cls, "__dataclass_fields__", {}))
    return {key: value for key, value in data.items() if key in field_names}


def _default_reliability(source_type: str) -> float:
    return {
        "observed_experiment": 0.95,
        "imported_trace": 0.8,
        "inferred_from_tools": 0.55,
        "inferred_from_tasks": 0.5,
        "user_declared": 0.25,
        "benchmark_reference": 0.2,
        "curated_research_reference": 0.2,
        "synthetic_sample": 0.35,
        "missing": 0.0,
    }.get(source_type, 0.0)
