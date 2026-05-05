from __future__ import annotations

import re
from dataclasses import dataclass

from contract2agent.evaluation.registry import AgentTypeRegistry
from contract2agent.evaluation.schema import (
    AgentClassification,
    AgentProfile,
    AgentTypeDefinition,
    CapabilitySignal,
)


_PRIMARY_THRESHOLD = 0.42
_SECONDARY_THRESHOLD = 0.28
_LOW_SIGNAL_THRESHOLD = 0.1


@dataclass
class _TypeScore:
    type_id: str
    confidence: float
    positive_signals: list[CapabilitySignal]
    negative_signals: list[CapabilitySignal]


class CapabilityClassifier:
    """General signal-based classifier that deliberately ignores agent identity."""

    def __init__(self, registry: AgentTypeRegistry | None = None) -> None:
        self.registry = registry or AgentTypeRegistry.default()

    def classify(self, profile: AgentProfile) -> AgentClassification:
        scores = [
            self._score_type(profile, definition)
            for definition in self.registry.non_unknown()
        ]
        scores.sort(key=lambda score: (-score.confidence, score.type_id))

        primary_types = [
            score.type_id
            for score in scores
            if score.confidence >= _PRIMARY_THRESHOLD
        ]
        secondary_types = [
            score.type_id
            for score in scores
            if _SECONDARY_THRESHOLD <= score.confidence < _PRIMARY_THRESHOLD
        ]
        rejected_types = [
            score.type_id
            for score in scores
            if score.negative_signals and score.confidence < _SECONDARY_THRESHOLD
        ]

        if not primary_types:
            low_signal_types = [
                score.type_id
                for score in scores
                if score.confidence >= _LOW_SIGNAL_THRESHOLD
            ]
            primary_types = ["unknown_agent"]
            secondary_types = [
                type_id for type_id in low_signal_types if type_id != "unknown_agent"
            ][:3]

        confidence_by_type = {
            score.type_id: round(score.confidence, 3)
            for score in scores
            if score.confidence >= _LOW_SIGNAL_THRESHOLD
        }
        if "unknown_agent" in primary_types:
            confidence_by_type["unknown_agent"] = round(
                0.82 if not confidence_by_type else 0.58,
                3,
            )

        matched_signals = {
            score.type_id: score.positive_signals
            for score in scores
            if score.positive_signals
        }
        negative_signals = {
            score.type_id: score.negative_signals
            for score in scores
            if score.negative_signals
        }
        risk_flags = self._risk_flags(profile, primary_types, secondary_types)
        missing_evidence = self._missing_evidence(profile, primary_types)

        return AgentClassification(
            primary_types=primary_types,
            secondary_types=secondary_types,
            rejected_types=sorted(set(rejected_types)),
            confidence_by_type=confidence_by_type,
            matched_signals=matched_signals,
            negative_signals=negative_signals,
            risk_flags=risk_flags,
            missing_evidence=missing_evidence,
            explanation=self._explanation(primary_types, secondary_types, confidence_by_type),
        )

    def _score_type(
        self,
        profile: AgentProfile,
        definition: AgentTypeDefinition,
    ) -> _TypeScore:
        declared_text = _normalize_text(
            [
                profile.description,
                *profile.declared_capabilities,
                *profile.allowed_actions,
                *profile.policy_constraints,
            ]
        )
        tool_text = _normalize_text(_tool_signal_text(profile))
        task_text = _normalize_text(profile.sample_tasks)
        negative_text = _normalize_text(
            [
                *profile.forbidden_actions,
                *profile.policy_constraints,
                profile.description,
            ]
        )

        signals: list[CapabilitySignal] = []
        negative_signals: list[CapabilitySignal] = []
        confidence = definition.default_confidence

        for match in _matches(definition.capability_signals, declared_text):
            signals.append(
                _signal(
                    definition.type_id,
                    "declared_capability",
                    "description/declared_capabilities",
                    match,
                    match,
                    "low",
                    0.08,
                    "Declared descriptions are weak evidence until tools, tasks, or results support them.",
                )
            )
        for match in _matches(definition.tool_signals, tool_text):
            signals.append(
                _signal(
                    definition.type_id,
                    "tool_surface",
                    "tools/tool_permissions/data_access",
                    match,
                    match,
                    "medium",
                    0.17,
                    "Tool and permission surfaces are stronger capability evidence than labels.",
                )
            )
        for match in _matches(definition.task_signals, task_text):
            signals.append(
                _signal(
                    definition.type_id,
                    "sample_task",
                    "sample_tasks",
                    match,
                    match,
                    "medium",
                    0.14,
                    "Representative sample tasks support capability inference.",
                )
            )
        for match in _matches(definition.negative_signals, negative_text):
            negative_signals.append(
                _signal(
                    definition.type_id,
                    "negative_signal",
                    "forbidden_actions/policy_constraints",
                    match,
                    match,
                    "medium",
                    0.2,
                    "Negative policy or constraint signals reduce this classification.",
                )
            )

        flag_signals = self._profile_flag_signals(profile, definition)
        signals.extend(flag_signals)

        confidence += min(
            0.2,
            sum(signal.confidence for signal in signals if signal.source_field.startswith("description")),
        )
        confidence += min(
            0.46,
            sum(signal.confidence for signal in signals if signal.source_field.startswith("tools")),
        )
        confidence += min(
            0.34,
            sum(signal.confidence for signal in signals if signal.source_field == "sample_tasks"),
        )
        confidence += min(
            0.28,
            sum(signal.confidence for signal in signals if signal.source_field == "profile_flags"),
        )
        confidence -= min(0.32, sum(signal.confidence for signal in negative_signals))
        confidence = max(0.0, min(0.96, confidence))

        return _TypeScore(
            type_id=definition.type_id,
            confidence=confidence,
            positive_signals=sorted(signals, key=lambda signal: signal.signal_id),
            negative_signals=sorted(negative_signals, key=lambda signal: signal.signal_id),
        )

    def _profile_flag_signals(
        self,
        profile: AgentProfile,
        definition: AgentTypeDefinition,
    ) -> list[CapabilitySignal]:
        signals: list[CapabilitySignal] = []
        type_id = definition.type_id
        if type_id == "coding_agent":
            if profile.can_write_files:
                signals.append(_flag_signal(type_id, "can_write_files", "code editing", 0.1))
            if profile.can_run_code:
                signals.append(_flag_signal(type_id, "can_run_code", "test or build execution", 0.12))
            if profile.can_read_files:
                signals.append(_flag_signal(type_id, "can_read_files", "repository inspection", 0.05))
        elif type_id == "file_reading_agent":
            if profile.can_read_files:
                signals.append(_flag_signal(type_id, "can_read_files", "file reading", 0.17))
            if profile.can_read_files and not profile.can_write_files:
                signals.append(_flag_signal(type_id, "read_only_files", "read-only file access", 0.07))
        elif type_id == "browser_navigation_agent":
            if profile.can_use_browser:
                signals.append(_flag_signal(type_id, "can_use_browser", "browser operation", 0.18))
            if profile.can_use_network:
                signals.append(_flag_signal(type_id, "can_use_network", "web access", 0.05))
        elif type_id == "financial_transaction_agent_simulated":
            if profile.can_execute_transactions:
                signals.append(_flag_signal(type_id, "can_execute_transactions", "transaction-like action surface", 0.22))
            if profile.requires_human_approval:
                signals.append(_flag_signal(type_id, "requires_human_approval", "approval boundary", 0.05))
        elif type_id == "general_tool_use_agent":
            if profile.tools:
                signals.append(_flag_signal(type_id, "tools_present", "generic tool-use surface", 0.22))
        elif type_id == "research_agent":
            if profile.can_use_network:
                signals.append(_flag_signal(type_id, "can_use_network", "source discovery", 0.07))
            if profile.can_read_files:
                signals.append(_flag_signal(type_id, "can_read_files", "source reading", 0.05))
        return signals

    def _missing_evidence(
        self,
        profile: AgentProfile,
        primary_types: list[str],
    ) -> list[str]:
        missing: list[str] = []
        if not profile.tools:
            missing.append("Tool surface is missing.")
        if not profile.sample_tasks:
            missing.append("Representative sample tasks are missing.")
        if not profile.declared_capabilities and not profile.description:
            missing.append("Declared capability or description is missing.")
        if profile.autonomy_level == "unknown":
            missing.append("Autonomy level is unknown.")
        if "unknown_agent" in primary_types:
            missing.append(
                "Insufficient tool/task/permission evidence for a non-unknown primary classification."
            )
        missing.append("No observed experiment or imported trace evidence was supplied.")
        return sorted(set(missing))

    def _risk_flags(
        self,
        profile: AgentProfile,
        primary_types: list[str],
        secondary_types: list[str],
    ) -> list[str]:
        type_ids = set(primary_types) | set(secondary_types)
        flags: set[str] = set()
        if profile.can_write_files or profile.can_run_code:
            flags.add("filesystem_or_code_execution")
        if profile.can_use_browser or profile.can_use_network:
            flags.add("network_or_browser_access")
        if profile.can_modify_external_state:
            flags.add("external_state_modification")
        if profile.can_execute_transactions:
            flags.add("transaction_like_action_surface")
            flags.add("high_risk_action_surface")
        if profile.requires_human_approval:
            flags.add("human_approval_required")
        if profile.autonomy_level.casefold() in {"high", "full", "autonomous"}:
            flags.add("high_autonomy")
        for data_access in profile.data_access:
            if any(token in data_access.casefold() for token in ("private", "secret", "customer", "personal")):
                flags.add("private_or_sensitive_data_access")
        for tool in profile.tools:
            if tool.modifies_state():
                flags.add("external_state_modification")
            if tool.side_effect_level.casefold() in {"high", "external"}:
                flags.add("high_risk_action_surface")
            if tool.requires_approval:
                flags.add("human_approval_required")
            if tool.can_access_private_data:
                flags.add("private_or_sensitive_data_access")
            for tag in tool.risk_tags:
                if tag:
                    flags.add(f"tool_risk:{tag}")
        if "financial_transaction_agent_simulated" in type_ids:
            flags.add("financial_transaction_simulation_only")
            flags.add("explicit_approval_required")
            flags.add("high_risk_action_surface")
        return sorted(flags)

    def _explanation(
        self,
        primary_types: list[str],
        secondary_types: list[str],
        confidence_by_type: dict[str, float],
    ) -> str:
        if primary_types == ["unknown_agent"]:
            return (
                "Classification remains unknown because supplied evidence does not "
                "include enough concrete tools, permissions, sample tasks, or observed traces."
            )
        pieces = [f"primary={', '.join(primary_types)}"]
        if secondary_types:
            pieces.append(f"secondary={', '.join(secondary_types)}")
        confidence = ", ".join(
            f"{type_id}:{value:.2f}"
            for type_id, value in sorted(confidence_by_type.items())
        )
        pieces.append(f"confidence from non-name signals: {confidence}")
        return "; ".join(pieces)


def _tool_signal_text(profile: AgentProfile) -> list[str]:
    values: list[str] = []
    for tool in profile.tools:
        values.extend(
            [
                tool.name,
                tool.category,
                tool.mode,
                tool.scope,
                tool.side_effect_level,
                *tool.risk_tags,
                *tool.evidence,
            ]
        )
    values.extend(profile.tool_permissions)
    values.extend(profile.data_access)
    values.extend(profile.allowed_actions)
    return values


def _signal(
    type_id: str,
    signal_kind: str,
    source_field: str,
    matched_value: str,
    capability: str,
    strength: str,
    confidence: float,
    explanation: str,
) -> CapabilitySignal:
    safe_value = re.sub(r"[^a-z0-9]+", "_", matched_value.casefold()).strip("_")
    return CapabilitySignal(
        signal_id=f"{type_id}:{signal_kind}:{safe_value}",
        label=matched_value,
        source_field=source_field,
        matched_value=matched_value,
        capability=capability,
        strength=strength,
        confidence=confidence,
        explanation=explanation,
    )


def _flag_signal(type_id: str, flag: str, capability: str, confidence: float) -> CapabilitySignal:
    return CapabilitySignal(
        signal_id=f"{type_id}:profile_flag:{flag}",
        label=flag,
        source_field="profile_flags",
        matched_value=flag,
        capability=capability,
        strength="medium",
        confidence=confidence,
        explanation="Profile permission flags support capability inference but do not prove performance.",
    )


def _normalize_text(values: list[str]) -> str:
    return " ".join(str(value).casefold() for value in values if value)


def _matches(signals: list[str], text: str) -> list[str]:
    matched: list[str] = []
    for signal in signals:
        normalized = signal.casefold()
        pattern = r"(?<![a-z0-9])" + re.escape(normalized).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
        if re.search(pattern, text):
            matched.append(signal)
    return matched
