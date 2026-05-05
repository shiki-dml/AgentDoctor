from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, TypeVar


JsonObject = dict[str, Any]
T = TypeVar("T")


@dataclass
class FileReadingAgentProfile:
    agent_id: str
    name: str
    description: str = ""
    declared_capabilities: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    tool_permissions: list[str] = field(default_factory=list)
    can_list_files: bool = False
    can_search_files: bool = False
    can_read_files: bool = False
    can_read_binary_files: bool = False
    can_read_pdf: bool = False
    can_access_repo: bool = False
    can_access_external_paths: bool = False
    can_use_network: bool = False
    can_write_files: bool = False
    can_run_shell: bool = False
    requires_human_approval: bool = False
    citation_support: str = "unknown"
    output_schema_support: str = "unknown"
    trace_support: str = "unknown"
    policy_constraints: list[str] = field(default_factory=list)
    metadata: JsonObject = field(default_factory=dict)


@dataclass
class DocumentRecord:
    file_id: str
    relative_path: str
    absolute_path_sanitized: str
    file_type: str
    mime_type: str
    size_bytes: int
    sha256: str
    line_count: int
    section_headings: list[str] = field(default_factory=list)
    chunk_count: int = 0
    allowed: bool = True
    tags: list[str] = field(default_factory=list)
    source: str = "local"
    metadata: JsonObject = field(default_factory=dict)


@dataclass
class CorpusManifest:
    corpus_id: str
    root_path: str
    documents: list[DocumentRecord] = field(default_factory=list)
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    source_type: str = "local"
    created_at: str = ""
    hash: str = ""
    metadata: JsonObject = field(default_factory=dict)
    provenance: str = ""
    license: str = ""
    limitations: list[str] = field(default_factory=list)


@dataclass
class EvidenceSpan:
    file_id: str
    line_start: int | None = None
    line_end: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    quote: str = ""
    label: str = ""
    required: bool = True


@dataclass
class FileReadingTask:
    task_id: str
    task_type: str
    question: str
    instructions: str = ""
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    supporting_files: list[str] = field(default_factory=list)
    distractor_files: list[str] = field(default_factory=list)
    gold_answer: str = ""
    gold_answer_aliases: list[str] = field(default_factory=list)
    gold_evidence_spans: list[EvidenceSpan] = field(default_factory=list)
    expected_citations: list[EvidenceSpan] = field(default_factory=list)
    unanswerable: bool = False
    negative_checks: list[str] = field(default_factory=list)
    grading_profile: str = "deterministic_v1"
    difficulty: str = "smoke"
    metadata: JsonObject = field(default_factory=dict)


@dataclass
class TargetAgentInput:
    task_id: str
    question: str
    corpus_dir: str
    manifest_path: str
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    instructions: str = ""
    required_output_schema: JsonObject = field(default_factory=dict)
    metadata: JsonObject = field(default_factory=dict)


@dataclass
class Citation:
    file_id: str
    line_start: int | None = None
    line_end: int | None = None
    quote: str = ""
    explanation: str = ""


@dataclass
class TargetAgentOutput:
    answer: str = ""
    citations: list[Citation] = field(default_factory=list)
    confidence: float | None = None
    files_read: list[str] = field(default_factory=list)
    notes: str = ""
    raw_output: str = ""
    schema_valid: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class FileAccessTrace:
    task_id: str
    files_read: list[str] = field(default_factory=list)
    files_referenced: list[str] = field(default_factory=list)
    forbidden_files_touched: list[str] = field(default_factory=list)
    stdout_path: str = ""
    stderr_path: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    timeout: bool = False
    command: list[str] = field(default_factory=list)
    exit_code: int | None = None
    metadata: JsonObject = field(default_factory=dict)


@dataclass
class FileReadingRun:
    run_id: str
    agent_profile: FileReadingAgentProfile
    corpus_manifest: CorpusManifest
    task_file: str
    tasks: list[FileReadingTask] = field(default_factory=list)
    outputs: dict[str, TargetAgentOutput] = field(default_factory=dict)
    traces: dict[str, FileAccessTrace] = field(default_factory=dict)
    started_at: str = ""
    finished_at: str = ""
    time_budget_seconds: float = 0.0
    max_tasks: int | None = None
    seed: int = 0
    status: str = "created"
    metadata: JsonObject = field(default_factory=dict)


@dataclass
class FileReadingGrade:
    task_id: str
    answer_score: float = 0.0
    answer_exact_match: bool = False
    answer_f1: float = 0.0
    citation_score: float = 0.0
    citation_presence: float = 0.0
    citation_span_accuracy: float = 0.0
    citation_quote_match: float = 0.0
    supporting_file_recall: float = 0.0
    supporting_file_precision: float = 0.0
    forbidden_file_violation: bool = False
    unanswerable_abstention_score: float = 1.0
    unsupported_claim_rate: float = 0.0
    schema_score: float = 0.0
    latency_score: float = 0.0
    robustness_tags: list[str] = field(default_factory=list)
    total_score: float = 0.0
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: JsonObject = field(default_factory=dict)


@dataclass
class FileReadingScorecard:
    run_id: str
    overall_score: float | None = None
    confidence: float = 0.0
    coverage: float = 0.0
    scores_by_dimension: dict[str, float] = field(default_factory=dict)
    task_type_scores: dict[str, float] = field(default_factory=dict)
    safety_score: float = 0.0
    citation_score: float = 0.0
    answer_score: float = 0.0
    robustness_score: float = 0.0
    efficiency_score: float = 0.0
    failure_modes: list[str] = field(default_factory=list)
    recommended_changes: list[str] = field(default_factory=list)
    next_eval_plan: list[str] = field(default_factory=list)


@dataclass
class ReferenceSource:
    source_id: str
    title: str
    source_type: str
    domain: str = ""
    source_url: str = ""
    local_path: str = ""
    license: str = ""
    provenance: str = ""
    reliability: float = 0.0
    applicable_task_types: list[str] = field(default_factory=list)
    metrics_available: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class ReferenceResult:
    reference_result_id: str
    source_id: str
    agent_or_model: str
    agent_config_summary: str = ""
    task_pack_id: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    environment: str = ""
    scoring_method: str = ""
    comparable_conditions: bool = False
    source_url: str = ""
    citation: str = ""
    limitations: list[str] = field(default_factory=list)


@dataclass
class ComparisonReport:
    target_run_id: str
    reference_results: list[ReferenceResult] = field(default_factory=list)
    comparable: bool = False
    compatibility_notes: list[str] = field(default_factory=list)
    metric_deltas: dict[str, float] = field(default_factory=dict)
    contextual_findings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    markdown_summary: str = ""


def to_dict(value: Any) -> Any:
    """Return JSON-serializable data for file-reading eval dataclasses."""
    if is_dataclass(value):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dict(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def from_dict(cls: type[T], data: JsonObject) -> T:
    return cls(**_coerce_fields(cls, data))


def _coerce_fields(cls: type, data: JsonObject) -> JsonObject:
    field_names = set(getattr(cls, "__dataclass_fields__", {}))
    filtered = {key: value for key, value in dict(data).items() if key in field_names}
    if cls is CorpusManifest:
        filtered["documents"] = [
            from_dict(DocumentRecord, item) for item in filtered.get("documents", [])
        ]
    elif cls is FileReadingTask:
        filtered["gold_evidence_spans"] = [
            from_dict(EvidenceSpan, item)
            for item in filtered.get("gold_evidence_spans", [])
        ]
        filtered["expected_citations"] = [
            from_dict(EvidenceSpan, item)
            for item in filtered.get("expected_citations", [])
        ]
    elif cls is TargetAgentOutput:
        filtered["citations"] = [
            from_dict(Citation, item) for item in filtered.get("citations", [])
        ]
    elif cls is FileReadingRun:
        filtered["agent_profile"] = from_dict(
            FileReadingAgentProfile,
            filtered["agent_profile"],
        )
        filtered["corpus_manifest"] = from_dict(
            CorpusManifest,
            filtered["corpus_manifest"],
        )
        filtered["tasks"] = [
            from_dict(FileReadingTask, item) for item in filtered.get("tasks", [])
        ]
        filtered["outputs"] = {
            str(task_id): from_dict(TargetAgentOutput, item)
            for task_id, item in filtered.get("outputs", {}).items()
        }
        filtered["traces"] = {
            str(task_id): from_dict(FileAccessTrace, item)
            for task_id, item in filtered.get("traces", {}).items()
        }
    elif cls is ComparisonReport:
        filtered["reference_results"] = [
            from_dict(ReferenceResult, item)
            for item in filtered.get("reference_results", [])
        ]
    return filtered
