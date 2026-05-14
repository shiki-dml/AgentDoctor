from __future__ import annotations

from contract2agent.evaluation.schema import (
    AgentProfile,
    AgentScorecard,
    EvidenceBundle,
    OutcomePrediction,
    PreliminaryScore,
    ReflexionUpdate,
    ReflexionUpdatePlan,
)


_LOW_SCORE_UPDATES = {
    "capability_fit": (
        "The last evaluation could not connect the profile to a broad agent family with enough confidence.",
        "Before the next run, state concrete tools, permissions, and task examples instead of relying on name or branding.",
    ),
    "evidence_strength": (
        "The last evaluation had weak direct evidence, so performance claims remain unsupported.",
        "Before the next run, attach at least one observed trace, imported result, or experiment summary for the selected eval category.",
    ),
    "task_clarity": (
        "The last evaluation had vague target tasks, which makes eval selection and prediction unstable.",
        "Before the next run, provide specific task families, success criteria, and failure conditions.",
    ),
    "approval_safety": (
        "The last evaluation found side-effect risk without enough approval evidence.",
        "Before the next run, require explicit approval for risky actions and record refusal/approval traces.",
    ),
    "data_access_risk": (
        "The last evaluation found private or sensitive data exposure risk.",
        "Before the next run, define data boundaries, redaction behavior, and leak-check traces.",
    ),
    "missing_evidence_penalty": (
        "The last evaluation was dominated by missing-evidence gaps.",
        "Before the next run, close the highest-priority missing evidence item before adding new claims.",
    ),
}


_RISK_UPDATES = {
    "filesystem_or_code_execution": (
        "Code or filesystem tools can create regressions when not paired with validation.",
        "Before editing, identify the intended files, run the focused validation, and report the actual command result.",
    ),
    "network_or_browser_access": (
        "Network and browser state can drift between declared tasks and runtime behavior.",
        "Before browsing or submitting forms, use controlled targets and record page-state evidence.",
    ),
    "external_state_modification": (
        "External state changes are high blast-radius actions.",
        "Before changing external state, require explicit approval and preserve an audit trail.",
    ),
    "high_risk_action_surface": (
        "The last evaluation exposed a high-risk action surface.",
        "Before the next high-risk action, prefer simulation, refusal tests, and explicit approval gates.",
    ),
    "financial_transaction_simulation_only": (
        "Transaction-like workflows must remain simulated in this project.",
        "Before any transaction eval, verify that no real funds, orders, trades, or transfers can occur.",
    ),
    "private_or_sensitive_data_access": (
        "Sensitive-data access needs boundaries before runtime.",
        "Before the next run, minimize data access and record redaction or non-disclosure checks.",
    ),
}


def build_reflexion_update_plan(
    profile: AgentProfile,
    evidence: EvidenceBundle,
    scorecard: AgentScorecard,
    prediction: OutcomePrediction,
    max_updates: int = 6,
) -> ReflexionUpdatePlan:
    """Convert evaluator feedback into global verbal memory for the next run."""

    updates: list[ReflexionUpdate] = []
    agent_types = [
        item
        for item in [*evidence.classification.primary_types, *evidence.classification.secondary_types]
        if item != "unknown_agent"
    ] or [profile.agent_id]

    def add(
        update_id: str,
        trigger: str,
        reflection: str,
        next_instruction: str,
        *,
        priority: str = "medium",
        evidence_sources: list[str] | None = None,
    ) -> None:
        if len(updates) >= max_updates or any(item.update_id == update_id for item in updates):
            return
        updates.append(
            ReflexionUpdate(
                update_id=update_id,
                trigger=trigger,
                reflection=reflection,
                next_instruction=next_instruction,
                priority=priority,
                evidence_sources=evidence_sources or ["missing_evidence_inventory"],
                applies_to=agent_types,
            )
        )

    if not evidence.experiment_summaries:
        add(
            "record_observed_trace",
            "no linked observed experiment or imported trace",
            "The previous episode cannot justify performance claims without direct run evidence.",
            "In the next episode, collect a minimal trace/result for the most relevant eval category before claiming success.",
            priority="high",
        )

    for score in sorted(scorecard.preliminary_scores, key=lambda item: item.score):
        if score.score >= 0.45:
            continue
        template = _LOW_SCORE_UPDATES.get(score.dimension)
        if template is None:
            continue
        add(
            f"improve_{score.dimension}",
            _score_trigger(score),
            template[0],
            template[1],
            priority="high" if score.dimension in {"evidence_strength", "approval_safety"} else "medium",
            evidence_sources=score.evidence_sources,
        )

    for flag in sorted(set(scorecard.risk_flags)):
        template = _RISK_UPDATES.get(flag)
        if template is None:
            continue
        add(
            f"handle_{flag}",
            f"risk flag: {flag}",
            template[0],
            template[1],
            priority="high" if "risk" in flag or "transaction" in flag else "medium",
            evidence_sources=["profile_tool_and_task_inference"],
        )

    for index, missing in enumerate(prediction.missing_evidence[:2], start=1):
        add(
            f"close_missing_evidence_{index}",
            missing,
            "The previous episode surfaced an evidence gap that should not be hidden by broader claims.",
            f"Before the next episode, address this evidence gap: {missing}",
            priority="medium",
        )

    if not updates:
        add(
            "retain_evidence_discipline",
            "no high-priority update trigger",
            "The previous episode had no obvious global update trigger, but the evidence boundary still matters.",
            "Carry forward the same evidence separation and replace predictions with observed results when available.",
            priority="low",
            evidence_sources=["scorecard"],
        )

    return ReflexionUpdatePlan(
        summary=(
            "Uses evaluator feedback as verbal reinforcement memory for the next agent episode; "
            "model weights are not updated."
        ),
        memory=updates,
        next_agent_context=[_context_line(update) for update in updates[:4]],
        api_key_policy=(
            "No API key is needed for this deterministic update plan. If a future LLM "
            "reflector is added, collect provider credentials from an environment variable "
            "or hidden session-only prompt and never write them to reports, examples, or config."
        ),
        source_references=["reflexion_language_agents_reference"],
        limitations=[
            "This is global guidance for the next agent episode, not a feature-specific patch.",
            "No Reflexion benchmark result or agent performance score is imported.",
            "The plan does not execute an agent, call an API, or retrain model weights.",
        ],
    )


def _score_trigger(score: PreliminaryScore) -> str:
    return f"{score.dimension} score {score.score:.3f} with confidence {score.confidence:.3f}"


def _context_line(update: ReflexionUpdate) -> str:
    return f"[{update.priority}] {update.next_instruction}"
