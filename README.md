# Contract2Agent

Contract-driven diagnosis and repair suggestions for LLM agents.

Contract2Agent is a lightweight offline CLI tool for diagnosing LLM agent
behavior from contracts and execution traces. It checks traces against behavior
contracts, explains loose or strict rules, highlights checker/parser/monitor
gaps, and produces repair suggestions such as patch previews, rule coverage,
and regression traces.

## At a Glance

| Capability | What you get |
|---|---|
| Trace diagnosis | See where the agent's tool flow diverged from the contract. |
| Strictness checks | Distinguish too-loose rules from too-strict rules and checkers. |
| Repair suggestions | Review suggested contract, checker, prompt, or eval changes. |
| Rule coverage | Spot rules that lack positive or negative trace coverage. |
| Regression traces | Generate focused traces that reproduce the diagnosed gap. |
| Static playground | Try a browser-side preview without uploading data. |

## Quickstart

Install from a local checkout:

```bash
python -m pip install -e ".[dev]"
```

Create and diagnose the built-in offline demo:

```bash
c2a demo --out demo_project
c2a counterexamples demo_project/agent_contract.yaml --out demo_project/traces/counterexamples
c2a check-all --contract demo_project/agent_contract.yaml --traces demo_project/traces/counterexamples --diagnose
```

For an existing project, start with triage or a quick diagnosis:

```bash
c2a triage --agent ./agent.yaml
c2a quick --contract ./agent_contract.yaml
c2a deep --rounds 3 --review on-fail --contract ./agent_contract.yaml
```

Use `c2a` for the CLI. The Python distribution and import package are both
`contract2agent`. A legacy `agentdoctor` console-script alias is still retained
for backward compatibility with existing local installs.

## Example Diagnosis

```text
ATD001 [error]
Category: contract_too_loose
Strictness: too_loose
Affected part: error_handling

Cause:
pdf_reader returned file_not_found, but markdown_writer was still called.

Suggested fix:
Add a rule forbidding markdown_writer after pdf_reader returns file_not_found.
```

## What It Diagnoses

- `contract_too_loose`
- `contract_too_strict`
- `checker_too_loose`
- `checker_too_strict`
- `monitor_too_loose`
- `monitor_too_strict`
- `parser_missed_constraint`
- `contract_conflict`
- `rule_uncovered`
- `eval_expectation_too_strict`

## Docs and Playground

- [Documentation home](docs/index.md)
- [Getting started](docs/getting-started.md)
- [CLI reference](docs/cli.md)
- [Interactive playground](docs/playground.md)

The playground is a static browser-side preview. Full analysis runs through the
local CLI.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

For docs work:

```bash
python -m pip install -e ".[docs]"
python scripts/check_docs_links.py
python -m mkdocs build --strict
```

## Limitations

- Patch suggestions are previews, not automatically applied by the playground.
- The static playground covers a small deterministic subset of the CLI behavior.
- Full diagnosis, report writing, and regression trace generation run locally
  through the CLI.

## License

No license file is currently included in this repository.
