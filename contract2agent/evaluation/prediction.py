from __future__ import annotations

from contract2agent.evaluation.schema import (
    AgentProfile,
    AgentScorecard,
    EvidenceBundle,
    OutcomePrediction,
)


class PredictionEngine:
    def predict(
        self,
        profile: AgentProfile,
        evidence: EvidenceBundle,
        scorecard: AgentScorecard,
        target_context: str = "general target workflow",
    ) -> OutcomePrediction:
        missing = sorted(set([*evidence.missing_evidence, *scorecard.missing_evidence]))
        risk_flags = sorted(set([*evidence.classification.risk_flags, *scorecard.risk_flags]))
        scores = scorecard.scores_by_dimension
        expected = scores.get("expected_reliability", 0.0)
        evidence_strength = scores.get("evidence_strength", 0.0)

        if (
            "unknown_agent" in evidence.classification.primary_types
            and not evidence.experiment_summaries
        ):
            return OutcomePrediction(
                predicted_success=None,
                confidence=0.05,
                likely_strengths=[],
                likely_failures=[
                    "insufficient profile detail",
                    "no observed experiment or trace evidence",
                ],
                risk_flags=risk_flags,
                evidence_basis=[
                    "unsupported claim: classification is unknown",
                    "declared description alone is not performance evidence",
                ],
                assumptions=[
                    "The agent may have capabilities that were not supplied in the profile.",
                ],
                missing_evidence=missing,
                recommended_next_tests=scorecard.recommended_next_evals,
                explanation=(
                    "Insufficient evidence to predict execution performance; complete "
                    "the profile and run at least one applicable eval category first."
                ),
                target_context=target_context,
            )

        confidence = round(
            max(
                0.05,
                min(
                    0.85,
                    scorecard.confidence * 0.45
                    + evidence_strength * 0.35
                    + scorecard.coverage * 0.2,
                ),
            ),
            3,
        )
        predicted = round(max(0.0, min(1.0, expected - self._risk_penalty(risk_flags))), 3)

        basis = [
            "low-confidence estimate" if confidence < 0.55 else "evidence-backed preliminary estimate",
            "classification uses tool, permission, task, and policy signals rather than agent name",
            "benchmark and methodology references are contextual, not direct scores",
        ]
        if any(
            source.source_type in {"observed_experiment", "imported_trace"}
            for source in evidence.data_sources
        ):
            basis.append("linked observed/imported evidence increased confidence")
        else:
            basis.append("no linked observed/imported experiment evidence is available")

        return OutcomePrediction(
            predicted_success=predicted,
            confidence=confidence,
            likely_strengths=self._likely_strengths(evidence, scores),
            likely_failures=self._likely_failures(evidence, risk_flags, missing),
            risk_flags=risk_flags,
            evidence_basis=basis,
            assumptions=[
                "Target tasks resemble the supplied sample tasks and selected eval categories.",
                "The deployment permissions match the supplied tool surface.",
                "No hidden tools or policies are added at runtime.",
            ],
            missing_evidence=missing,
            recommended_next_tests=scorecard.recommended_next_evals,
            explanation=self._explanation(predicted, confidence, risk_flags),
            target_context=target_context,
        )

    def _risk_penalty(self, risk_flags: list[str]) -> float:
        penalty = 0.0
        if "high_risk_action_surface" in risk_flags:
            penalty += 0.08
        if "external_state_modification" in risk_flags:
            penalty += 0.05
        if "financial_transaction_simulation_only" in risk_flags:
            penalty += 0.08
        if "high_autonomy" in risk_flags:
            penalty += 0.06
        if "human_approval_required" in risk_flags:
            penalty -= 0.03
        return max(0.0, penalty)

    def _likely_strengths(
        self,
        evidence: EvidenceBundle,
        scores: dict[str, float],
    ) -> list[str]:
        strengths: list[str] = []
        if scores.get("capability_fit", 0.0) >= 0.55:
            strengths.append("profile signals fit one or more broad agent types")
        if scores.get("task_clarity", 0.0) >= 0.7:
            strengths.append("sample tasks are specific enough to choose eval categories")
        if evidence.experiment_summaries:
            strengths.append("linked experiment summaries provide direct evidence")
        return strengths

    def _likely_failures(
        self,
        evidence: EvidenceBundle,
        risk_flags: list[str],
        missing: list[str],
    ) -> list[str]:
        failures: list[str] = []
        if not evidence.experiment_summaries:
            failures.append("prediction may not hold because no observed trace/result exists")
        if "network_or_browser_access" in risk_flags:
            failures.append("web or browser state may differ from declared tasks")
        if "filesystem_or_code_execution" in risk_flags:
            failures.append("code or filesystem changes may cause regressions without tests")
        if "financial_transaction_simulation_only" in risk_flags:
            failures.append("transaction workflow must remain simulated and approval-gated")
        if missing:
            failures.append("missing evidence may hide important failure modes")
        return sorted(set(failures))

    def _explanation(
        self,
        predicted: float,
        confidence: float,
        risk_flags: list[str],
    ) -> str:
        if confidence < 0.35:
            confidence_label = "low-confidence"
        elif confidence < 0.6:
            confidence_label = "moderate-confidence"
        else:
            confidence_label = "evidence-backed"
        risk_note = " Risk flags reduced the prediction." if risk_flags else ""
        return (
            f"{confidence_label} preliminary success estimate of {predicted:.2f}. "
            "This is not a guarantee and should be replaced by observed eval results."
            f"{risk_note}"
        )
