# Playground

Paste an agent contract and a sample trace. Contract2Agent will highlight likely
rule gaps, strictness problems, coverage gaps, and repair suggestions directly
in your browser.

!!! note "Privacy"
    This playground runs entirely in your browser. It does not upload your
    contract or trace. It is a lightweight static preview of Contract2Agent's
    diagnosis concepts; full analysis runs through the [local CLI](cli.md).

<noscript>
  <div class="ad-playground ad-playground--noscript">
    <p>This static playground needs JavaScript to run the in-browser checks. No input is uploaded when JavaScript is enabled.</p>
  </div>
</noscript>

<div class="ad-playground" data-contract2agent-playground>
  <section class="ad-playground__intro">
    <div>
      <p class="ad-kicker">Static browser-side preview</p>
      <h2>Explore a trace diagnosis</h2>
      <p>Choose a sample or paste your own JSON. The preview checks a focused subset of Contract2Agent behavior contracts without a backend, framework, or network call.</p>
    </div>
    <p id="ad-playground-status" class="ad-status ad-status--info" role="status" aria-live="polite">Choose a sample or paste your own contract, then click Analyze.</p>
  </section>

  <div class="ad-playground__shell">
    <section class="ad-panel ad-panel--inputs" aria-labelledby="ad-inputs-title">
      <div class="ad-panel__header">
        <div>
          <h3 id="ad-inputs-title">Inputs</h3>
          <p>Start from a sample scenario or use your own contract and trace JSON.</p>
        </div>
      </div>

      <div class="ad-field ad-field--sample">
        <label for="ad-sample-select">Sample scenario</label>
        <select id="ad-sample-select" class="ad-control">
          <option value="paper_reader_valid" selected>Valid read/write</option>
          <option value="missing_file_write">Missing file handling</option>
          <option value="forbidden_web_search">Forbidden web search</option>
          <option value="contract_conflict_markdown">Contract conflict</option>
          <option value="parser_missed_no_web">Missed no-web-search restriction</option>
        </select>
        <p id="ad-sample-description" class="ad-field__hint"></p>
      </div>

      <div class="ad-playground__actions" aria-label="Playground actions">
        <button type="button" id="ad-analyze-button" class="ad-button ad-button--primary">Analyze</button>
        <button type="button" id="ad-reset-button" class="ad-button">Reset sample</button>
        <button type="button" id="ad-copy-button" class="ad-button" disabled>Copy report JSON</button>
        <button type="button" id="ad-clear-button" class="ad-button ad-button--quiet">Clear</button>
      </div>

      <div class="ad-editor-stack">
        <section class="ad-editor-pane">
          <div class="ad-editor-pane__header">
            <label for="ad-contract-input">Agent contract JSON</label>
            <span>Required</span>
          </div>
          <textarea id="ad-contract-input" class="ad-textarea" spellcheck="false" rows="20" aria-describedby="ad-contract-help"></textarea>
          <p id="ad-contract-help" class="ad-field__hint">Use a JSON object with fields such as name, goal, tools, forbidden_tools, and rules.</p>
        </section>

        <section class="ad-editor-pane">
          <div class="ad-editor-pane__header">
            <label for="ad-trace-input">Trace JSON</label>
            <span>Optional</span>
          </div>
          <textarea id="ad-trace-input" class="ad-textarea" spellcheck="false" rows="20" aria-describedby="ad-trace-help"></textarea>
          <p id="ad-trace-help" class="ad-field__hint">Use a JSON array of events, or an object with an events array.</p>
        </section>
      </div>
    </section>

    <section class="ad-panel ad-panel--results" aria-labelledby="ad-results-title" aria-live="polite">
      <div class="ad-panel__header">
        <div>
          <h3 id="ad-results-title">Report Preview</h3>
          <p>Results are arranged for review first. Raw JSON stays at the bottom.</p>
        </div>
      </div>

      <div id="ad-empty-output" class="ad-empty-state">
        <strong>Ready when you are.</strong>
        <span>Choose a sample or paste your own contract, then click Analyze.</span>
      </div>

      <div id="ad-summary-output" class="ad-output-section"></div>
      <div id="ad-issues-output" class="ad-output-section"></div>
      <div id="ad-coverage-output" class="ad-output-section"></div>
      <div id="ad-patches-output" class="ad-output-section"></div>
      <div id="ad-regression-output" class="ad-output-section"></div>
      <div id="ad-json-output" class="ad-output-section"></div>
    </section>
  </div>
</div>

## Preview Scope

The playground checks a small deterministic subset of Contract2Agent concepts:

- contract field validation
- conflicts involving Markdown writing
- missing `no_write_on_missing_file` coverage
- traces that write after `pdf_reader` returns `file_not_found`
- forbidden tool calls
- parser-missed no-web-search restrictions
- simplified rule coverage

Patch previews and regression traces shown here are suggestions only. The page
never applies patches and never modifies files.
