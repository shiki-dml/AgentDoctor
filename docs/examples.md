# Examples

The repository includes sample files that show the intended GitHub-facing workflow without requiring external services.

## Example Dashboard

Start with `examples/README.md`.

## Paper Reader Agent

The paper reader agent example in `examples/paper-reader-agent/README.md` demonstrates:

- triage
- document reading
- tool-call order
- Markdown output
- missing-file handling
- source-grounding and hallucination risk

Files:

- `examples/paper-reader-agent/agent.yaml`
- `examples/paper-reader-agent/expected-report.md`

## Sample Reports

Sample reports are examples, not actual run outputs:

- Quick, deep, and auto report shapes are described in [Reports](reports.md).

Use them to understand report shape before running the CLI locally.

## Run the Built-In Offline Demo

Contract2Agent can also generate a deterministic demo project:

```bash
c2a demo --out demo_project
c2a counterexamples demo_project/agent_contract.yaml --out demo_project/traces/counterexamples
c2a check-all --contract demo_project/agent_contract.yaml --traces demo_project/traces/counterexamples --diagnose
```

The generated demo writes reports under `demo_project/reports/`.
