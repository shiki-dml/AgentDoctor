# Contract2Agent

<div class="ad-home">
  <section class="ad-hero">
    <p class="ad-kicker">Pre-runtime AI agent evaluation</p>
    <h1>Classify agent capabilities before deployment.</h1>
    <p class="ad-hero__lead">Contract2Agent turns agent descriptions, tools, permissions, sample tasks, traces, and source references into cautious preliminary evaluation reports.</p>
  </section>
</div>

[Try Agent Evaluation](agent-eval/index.html){ .md-button .md-button--primary }
[Legacy Contract Playground](playground/index.html){ .md-button }
[Read the Quickstart](getting-started.md){ .md-button }

## Why Use It

Agent claims are not performance evidence. A profile can say it edits code,
uses a browser, reads files, or handles transactions, but deployment decisions
need a clearer record of what is declared, what is inferred from tools and
tasks, what is actually observed, and what evidence is still missing.

Contract2Agent keeps those layers separate and turns them into a reviewable
Markdown or JSON report.

<div class="ad-feature-grid">
  <article class="ad-feature-card">
    <strong>Capability Classification</strong>
    <span>Infer broad agent families from tools, permissions, tasks, and constraints rather than names.</span>
  </article>
  <article class="ad-feature-card">
    <strong>Evidence Separation</strong>
    <span>Distinguish declared, inferred, observed, reference, and missing evidence.</span>
  </article>
  <article class="ad-feature-card">
    <strong>Eval Categories</strong>
    <span>Select broad next-test categories without pretending to run specialized graders.</span>
  </article>
  <article class="ad-feature-card">
    <strong>Preliminary Prediction</strong>
    <span>Estimate likely outcome with confidence, risk flags, assumptions, and missing evidence.</span>
  </article>
  <article class="ad-feature-card">
    <strong>Static Demo</strong>
    <span>Use the GitHub Pages demo without a backend, API key, or live benchmark fetch.</span>
  </article>
  <article class="ad-feature-card">
    <strong>Legacy Diagnosis</strong>
    <span>Preserve the contract-review playground as a specialized static demo path.</span>
  </article>
</div>

## Example Flow

| Stage | Step 1 | Step 2 | Step 3 |
| --- | --- | --- | --- |
| Profile signals | **Agent profile**<br>Description, tools, permissions | **Capability signals**<br>Tool and task evidence | **Agent type classification**<br>Broad family match |
| Evidence and report | **Evidence resolution**<br>Declared, observed, missing | **Eval categories**<br>Recommended next checks | **Preliminary prediction**<br>Confidence and risks |

## Start Here

- Want the new generalized path: open [Agent Evaluation](agent-eval/index.html).
- Want the legacy contract demo: open the [Playground](playground/index.html).
- Need exact commands and flags: use the [CLI Reference](cli.md).
- Reviewing older trace diagnosis categories: see [Failure Taxonomy](failure-taxonomy.md).

## Current Scope

Contract2Agent is lightweight and static-first. GitHub Pages demos are static
reporting and reasoning surfaces only; they do not run arbitrary experiments,
call LLM APIs, fetch live benchmark data, or execute financial transactions.
