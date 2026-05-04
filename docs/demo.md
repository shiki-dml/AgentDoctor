# Contract2Agent Interactive Demo

Diagnose agent configurations before deployment.
{: .c2a-demo-subtitle }

This browser-based demo lets you paste an agent configuration and preview Contract2Agent-style diagnostics, including risk score, failure taxonomy, minimal patch suggestions, estimated fix effort, regression trace, and rule coverage.

!!! note "Privacy and scope"
    This demo runs entirely in the browser using a lightweight demonstration rule set. It does not upload your configuration or call any external service. For the full production diagnosis, use the Contract2Agent CLI.

## How to Use

1. Choose an example or paste JSON.
2. Click **Diagnose**, or press **Ctrl+Enter** / **Cmd+Enter** inside the editor.
3. Review the risk score, patch preview, suggested fixes, and rule coverage.
4. Copy or download the report for review.

<noscript>
  <div class="c2a-demo c2a-demo--noscript">
    <p>This static demo needs JavaScript to run browser-side checks. When enabled, the diagnosis still runs locally in your browser.</p>
  </div>
</noscript>

<div class="c2a-demo" data-contract2agent-demo>
  <section class="c2a-demo__layout">
    <aside class="c2a-demo__panel c2a-demo__panel--input" aria-labelledby="c2a-demo-input-title">
      <div class="c2a-demo__panel-header">
        <div>
          <p class="c2a-demo__eyebrow">Configuration input</p>
          <h2 id="c2a-demo-input-title">Agent configuration editor</h2>
        </div>
        <p id="c2a-demo-input-status" class="c2a-demo__status" role="status" aria-live="polite">Ready.</p>
      </div>

      <div class="c2a-demo__field">
        <label for="c2a-demo-example-select">Example</label>
        <select id="c2a-demo-example-select" class="c2a-demo__select">
          <option value="valid_minimal_agent">Valid minimal agent</option>
          <option value="missing_tools">Missing tools</option>
          <option value="missing_fallback_route">Missing fallback route</option>
          <option value="unsafe_memory_retention">Unsafe memory retention</option>
          <option value="excessive_token_budget">Excessive token budget</option>
          <option value="missing_output_schema">Missing output schema</option>
          <option value="high_risk_combined" selected>High-risk combined example</option>
        </select>
      </div>

      <div class="c2a-demo__actions" aria-label="Configuration actions">
        <button type="button" id="c2a-demo-load-example" class="c2a-demo__button">Load Example</button>
        <button type="button" id="c2a-demo-diagnose" class="c2a-demo__button c2a-demo__button--primary">Diagnose</button>
        <button type="button" id="c2a-demo-format-json" class="c2a-demo__button">Format JSON</button>
        <button type="button" id="c2a-demo-clear" class="c2a-demo__button">Clear</button>
        <button type="button" id="c2a-demo-reset" class="c2a-demo__button c2a-demo__button--quiet">Reset Demo</button>
      </div>

      <div class="c2a-demo__field">
        <label for="c2a-demo-config-input">Agent configuration JSON</label>
        <textarea id="c2a-demo-config-input" class="c2a-demo__editor" spellcheck="false" rows="30" aria-describedby="c2a-demo-editor-help"></textarea>
        <p id="c2a-demo-editor-help" class="c2a-demo__hint">Use a JSON object. Press Ctrl+Enter or Cmd+Enter to diagnose.</p>
      </div>
    </aside>

    <section class="c2a-demo__panel c2a-demo__panel--report" aria-labelledby="c2a-demo-report-title">
      <div class="c2a-demo__panel-header">
        <div>
          <p class="c2a-demo__eyebrow">Browser diagnosis</p>
          <h2 id="c2a-demo-report-title">Diagnostic report</h2>
        </div>
        <p class="c2a-demo__privacy-note">Runs locally in your browser.</p>
      </div>

      <div class="c2a-demo__report-actions" aria-label="Report actions">
        <button type="button" id="c2a-demo-copy-json" class="c2a-demo__button" disabled>Copy JSON report</button>
        <button type="button" id="c2a-demo-copy-patch" class="c2a-demo__button" disabled>Copy minimal patch</button>
        <button type="button" id="c2a-demo-download-json" class="c2a-demo__button" disabled>Download JSON report</button>
        <button type="button" id="c2a-demo-download-md" class="c2a-demo__button" disabled>Download Markdown report</button>
      </div>

      <div id="c2a-demo-report-status" class="c2a-demo__status c2a-demo__status--info" role="status" aria-live="polite">Load an example or paste JSON, then run diagnosis.</div>

      <div id="c2a-demo-report-output" class="c2a-demo__report-output">
        <div class="c2a-demo__empty-state">
          <strong>No report yet.</strong>
          <span>Run a diagnosis to see risk score, failure taxonomy, minimal patch preview, regression trace, and rule coverage.</span>
        </div>
      </div>
    </section>
  </section>
</div>

## Demo Rule Set

This page uses a small deterministic browser-side rule set for demonstration:

- agent identity
- tool availability
- fallback routing
- memory retention safety
- token budget guardrails
- output schema
- evaluation policy
- human review gates for high-risk configurations

The CLI remains the source of truth for full Contract2Agent diagnosis.
