from __future__ import annotations

from contract2agent.evaluation.capability_classifier import CapabilityClassifier
from contract2agent.evaluation.evidence import EvidenceResolver
from contract2agent.evaluation.prediction import PredictionEngine
from contract2agent.evaluation.reflexion import build_reflexion_update_plan
from contract2agent.evaluation.registry import EvalCategoryRegistry
from contract2agent.evaluation.schema import (
    AgentEvaluationReport,
    AgentProfile,
    AgentScorecard,
    EvidenceBundle,
    EvidenceSource,
    ExperimentSummary,
    OutcomePrediction,
    to_dict,
)
from contract2agent.evaluation.scoring import ScoringEngine


class ReportRenderer:
    def to_dict(
        self,
        profile: AgentProfile,
        evidence: EvidenceBundle,
        scorecard: AgentScorecard,
        prediction: OutcomePrediction,
    ) -> dict:
        reflexion_plan = build_reflexion_update_plan(profile, evidence, scorecard, prediction)
        return {
            "agent_profile": to_dict(profile),
            "classification": to_dict(evidence.classification),
            "inferred_capabilities": inferred_capabilities(evidence),
            "applicable_eval_categories": to_dict(evidence.applicable_eval_categories),
            "evidence_summary": to_dict(evidence.data_sources),
            "preliminary_scores": to_dict(scorecard.preliminary_scores),
            "outcome_prediction": to_dict(prediction),
            "reflexion_update_plan": to_dict(reflexion_plan),
            "data_sources": to_dict(evidence.data_sources),
            "missing_evidence": sorted(set([*evidence.missing_evidence, *scorecard.missing_evidence])),
            "limitations": self._limitations(evidence, scorecard, prediction),
        }

    def render_markdown(
        self,
        profile: AgentProfile,
        evidence: EvidenceBundle,
        scorecard: AgentScorecard,
        prediction: OutcomePrediction,
    ) -> str:
        reflexion_plan = build_reflexion_update_plan(profile, evidence, scorecard, prediction)
        lines: list[str] = [
            "# Agent Evaluation Report",
            "",
            "## Agent Summary",
            f"- Agent id: `{profile.agent_id}`",
            f"- Name: {profile.name}",
            f"- Environment: {profile.environment}",
            f"- Autonomy level: {profile.autonomy_level}",
            "",
            "## Classified Agent Types",
            f"- Primary: {', '.join(evidence.classification.primary_types) or 'none'}",
            f"- Secondary: {', '.join(evidence.classification.secondary_types) or 'none'}",
            f"- Rejected: {', '.join(evidence.classification.rejected_types) or 'none'}",
            f"- Explanation: {evidence.classification.explanation}",
            "",
            "## Inferred Capabilities",
        ]
        lines.extend(_plain_list(inferred_capabilities(evidence), "No concrete capabilities inferred."))
        lines.append("")

        lines.append("## Matched Signals")
        if evidence.classification.matched_signals:
            for type_id, signals in sorted(evidence.classification.matched_signals.items()):
                details = [
                    f"{signal.source_field}:{signal.matched_value} ({signal.strength})"
                    for signal in signals
                ]
                lines.append(f"- `{type_id}`: {', '.join(details)}")
        else:
            lines.append("- No matched signals beyond sparse profile metadata.")
        lines.append("")

        lines.append("## Risk Flags")
        lines.extend(_plain_list(scorecard.risk_flags, "No risk flags identified from supplied data."))
        lines.append("")

        lines.append("## Applicable Eval Categories")
        for category in evidence.applicable_eval_categories:
            lines.append(f"- `{category.category_id}`: {category.label}")
            lines.append(f"  - Tests: {', '.join(category.what_it_tests)}")
            lines.append(f"  - Required evidence: {', '.join(category.required_evidence)}")
        if not evidence.applicable_eval_categories:
            lines.append("- No eval categories selected.")
        lines.append("")

        lines.append("## Preliminary Scorecard")
        for score in scorecard.preliminary_scores:
            lines.append(
                f"- `{score.dimension}`: score={score.score:.3f}, confidence={score.confidence:.3f}"
            )
            lines.append(f"  - Evidence: {', '.join(score.evidence_sources)}")
            lines.append(f"  - Explanation: {score.explanation}")
        lines.append("")

        lines.append("## Outcome Prediction")
        if prediction.predicted_success is None:
            lines.append("- Predicted success: unsupported by current evidence.")
        else:
            lines.append(f"- Predicted success: {prediction.predicted_success:.3f}")
        lines.append(f"- Confidence: {prediction.confidence:.3f}")
        lines.append(f"- Explanation: {prediction.explanation}")
        lines.extend(f"- Evidence basis: {basis}" for basis in prediction.evidence_basis)
        lines.append("")

        lines.append("## Global Reflexion Update Plan")
        lines.append(f"- Strategy: {reflexion_plan.strategy}")
        lines.append(f"- API required: {str(reflexion_plan.api_required).lower()}")
        lines.append(f"- Summary: {reflexion_plan.summary}")
        lines.append(f"- API key policy: {reflexion_plan.api_key_policy}")
        for update in reflexion_plan.memory:
            lines.append(f"- `{update.update_id}` ({update.priority}, {update.scope})")
            lines.append(f"  - Trigger: {update.trigger}")
            lines.append(f"  - Reflection: {update.reflection}")
            lines.append(f"  - Next instruction: {update.next_instruction}")
        lines.append("")

        lines.append("## Evidence Basis")
        for source in evidence.data_sources:
            location = f" ({source.url})" if source.url else ""
            lines.append(
                f"- `{source.source_id}` [{source.source_type}, reliability={source.reliability:.2f}]: {source.title}{location}"
            )
            if source.limitations:
                lines.append(f"  - Limitations: {'; '.join(source.limitations)}")
        lines.append("")

        lines.append("## Missing Evidence")
        lines.extend(_plain_list(sorted(set([*evidence.missing_evidence, *scorecard.missing_evidence])), "No missing evidence recorded."))
        lines.append("")

        lines.append("## Recommended Next Tests")
        lines.extend(_plain_list(prediction.recommended_next_tests, "No next tests recommended."))
        lines.append("")

        lines.append("## Limitations")
        lines.extend(_plain_list(self._limitations(evidence, scorecard, prediction), "No limitations recorded."))
        lines.append("")
        return "\n".join(lines)

    def build_report(
        self,
        profile: AgentProfile,
        evidence: EvidenceBundle,
        scorecard: AgentScorecard,
        prediction: OutcomePrediction,
    ) -> AgentEvaluationReport:
        report_json = self.to_dict(profile, evidence, scorecard, prediction)
        report_markdown = self.render_markdown(profile, evidence, scorecard, prediction)
        reflexion_plan = build_reflexion_update_plan(profile, evidence, scorecard, prediction)
        return AgentEvaluationReport(
            agent_profile=profile,
            classification=evidence.classification,
            inferred_capabilities=inferred_capabilities(evidence),
            applicable_eval_categories=evidence.applicable_eval_categories,
            evidence_summary=evidence.data_sources,
            preliminary_scores=scorecard.preliminary_scores,
            outcome_prediction=prediction,
            reflexion_update_plan=reflexion_plan,
            data_sources=evidence.data_sources,
            missing_evidence=report_json["missing_evidence"],
            limitations=report_json["limitations"],
            report_markdown=report_markdown,
            report_json=report_json,
        )

    def _limitations(
        self,
        evidence: EvidenceBundle,
        scorecard: AgentScorecard,
        prediction: OutcomePrediction,
    ) -> list[str]:
        limitations = [
            "This is a generalized preliminary evaluation, not a deep specialized grader.",
            "Declared and inferred capabilities are not proof of performance.",
            "Benchmark references are contextual and do not create direct scores.",
            "Outcome prediction is a confidence-scored estimate, not a guarantee.",
        ]
        if not evidence.experiment_summaries:
            limitations.append("No observed experiment or imported trace was linked to the agent.")
        if "financial_transaction_simulation_only" in evidence.classification.risk_flags:
            limitations.append("Financial transaction workflows are simulation-only.")
        limitations.extend(prediction.missing_evidence[:3])
        return sorted(set(limitations))


def evaluate_agent_profile(
    profile: AgentProfile,
    experiment_results: list[ExperimentSummary] | None = None,
    benchmark_references: list[EvidenceSource] | None = None,
    target_context: str = "general target workflow",
) -> tuple[EvidenceBundle, AgentScorecard, OutcomePrediction]:
    classification = CapabilityClassifier().classify(profile)
    evidence = EvidenceResolver(EvalCategoryRegistry.default()).resolve(
        profile,
        classification,
        experiment_results=experiment_results,
        benchmark_references=benchmark_references,
    )
    scorecard = ScoringEngine().score(evidence)
    prediction = PredictionEngine().predict(
        profile,
        evidence,
        scorecard,
        target_context=target_context,
    )
    scorecard.prediction_summary = _prediction_summary(prediction)
    return evidence, scorecard, prediction


def inferred_capabilities(evidence: EvidenceBundle) -> list[str]:
    capabilities: set[str] = set()
    for signals in evidence.classification.matched_signals.values():
        for signal in signals:
            capabilities.add(signal.capability)
    return sorted(capabilities)


def _prediction_summary(prediction: OutcomePrediction) -> str:
    if prediction.predicted_success is None:
        return "Unsupported by current evidence."
    return (
        f"Predicted success {prediction.predicted_success:.3f} "
        f"with confidence {prediction.confidence:.3f}."
    )


def _plain_list(values: list[str], empty: str) -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]
