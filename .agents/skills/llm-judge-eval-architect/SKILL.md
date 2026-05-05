---
name: llm-judge-eval-architect
description: Use this skill when adding optional LLM judge support to evaluation systems, including API key handling, provider abstraction, judge prompts, JSON judge outputs, token/cost controls, caching, and deterministic-vs-LLM score separation.
---

# LLM Judge Eval Architect Skill

## Purpose

Use this skill to add optional LLM-based judging to an evaluation framework without making API calls mandatory or undermining deterministic grading.

## Core Rules

1. Deterministic graders remain the default.
2. LLM judging must be explicitly enabled by the user.
3. Never expose API keys in browser code, logs, reports, or committed files.
4. Prefer environment variables for keys.
5. Use hidden CLI input for session-only keys.
6. Do not store keys unless explicitly requested and safe.
7. Do not make GitHub Pages call model APIs.
8. Mark LLM results as non-deterministic and judge-based.
9. Store model/provider/prompt version/token usage/cost estimate when available.
10. Cache judge results by task/output/evidence/model/prompt hash.
11. Send minimal context to reduce token usage.
12. Never send entire corpora by default.
13. Use structured JSON output where possible.
14. Validate judge output before using it.
15. If judge output is invalid, fall back to deterministic results and report the judge failure.

## LLM Judge Use Cases

Use LLM judging only for cases deterministic graders cannot handle well:

- Semantic equivalence
- Summary faithfulness
- Contradiction detection
- Open-ended answer quality
- Evidence-to-answer support checking
- Recommendation synthesis

Do not use LLM judge for:

- Citation quote match
- Line span existence
- Forbidden file violations
- Schema validation
- Timeout
- File hash checks
- Path containment

Those should be deterministic.

## Token Efficiency

Implement controls for:

- Max judge tasks
- Judge-only failed/uncertain/open-ended/all
- Max input chars
- Max output tokens
- Evidence snippet limit
- Cost budget
- Dry-run estimate
- Cache enabled/disabled
- Batch size if supported

## Judge Output Schema

Judge output should include:

- `semantic_correctness`
- `evidence_support`
- `contradiction_risk`
- `unsupported_claims`
- `recommendation_items`
- `confidence`
- `rationale`
- `limitations`

All fields must be validated.

## Final Response Expectation

When this skill is used, report:

1. Provider abstraction added.
2. API key handling behavior.
3. Token/cost controls.
4. Judge prompt and schema.
5. Cache behavior.
6. Tests added.
7. Deterministic fallback behavior.
