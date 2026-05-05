from __future__ import annotations

import json
import sys


def main() -> int:
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    payload = json.loads(open(input_path, encoding="utf-8").read())
    failures = set(payload.get("failure_modes") or [])
    semantic = 0.4 if "answer_incorrect" in failures else 0.85
    support = 0.35 if "missing_citation" in failures or "citation_quote_mismatch" in failures else 0.8
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "semantic_correctness_score": semantic,
                "evidence_support_score": support,
                "contradiction_risk": 0.1,
                "unsupported_claims": [],
                "missing_evidence_notes": [],
                "recommendation_items": ["Keep answer synthesis tied to quoted evidence."],
                "confidence": 0.6,
                "rationale": "Dummy local judge for CLI wiring tests.",
                "limitations": ["Not a real semantic judge."],
                "judge_model": "dummy-command-judge",
                "judge_provider": "command",
                "judge_based": True,
                "deterministic": False,
            },
            handle,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
