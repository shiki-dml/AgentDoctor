# AgentDoctor Playground

Try AgentDoctor in your browser. Paste an agent contract and optional trace, then run deterministic checks to see diagnosis-style feedback.

This playground runs entirely in your browser. It does not upload your contract or trace. It is a lightweight static preview of AgentDoctor's diagnosis concepts. For full analysis, run the [c2a CLI](cli.md) locally.

The playground is intentionally limited: it uses plain JavaScript, built-in JSON samples, and deterministic checks. It does not use a backend, database, login, LLM API, Python-in-browser runtime, Pyodide, React, or patch application.

<noscript>
  <div class="ad-playground ad-playground--noscript">
    <p>This static playground needs JavaScript to run the in-browser checks. No input is uploaded when JavaScript is enabled.</p>
  </div>
</noscript>

<div class="ad-playground" data-agentdoctor-playground>
  <div class="ad-playground__toolbar">
    <div class="ad-field ad-field--sample">
      <label for="ad-sample-select">Sample scenario</label>
      <select id="ad-sample-select" class="ad-control">
        <option value="paper_reader_valid" selected>Paper reader: valid read then write</option>
        <option value="missing_file_write">Missing file handling: write after file_not_found</option>
        <option value="forbidden_web_search">Forbidden web search</option>
        <option value="contract_conflict_markdown">Contract conflict: markdown_writer required but forbidden</option>
        <option value="parser_missed_no_web">Parser missed restriction: requirement says no web search but contract allows it</option>
      </select>
    </div>
    <div class="ad-playground__actions" aria-label="Playground actions">
      <button type="button" id="ad-analyze-button" class="ad-button ad-button--primary">Analyze</button>
      <button type="button" id="ad-reset-button" class="ad-button">Reset sample</button>
      <button type="button" id="ad-copy-button" class="ad-button" disabled>Copy report JSON</button>
      <button type="button" id="ad-clear-button" class="ad-button ad-button--quiet">Clear</button>
    </div>
  </div>

  <p id="ad-playground-status" class="ad-status" role="status" aria-live="polite">Choose a sample and click Analyze.</p>

  <div class="ad-editor-grid">
    <section class="ad-editor-pane">
      <div class="ad-editor-pane__header">
        <label for="ad-contract-input">Agent contract/config JSON</label>
        <span>Paste JSON, or use the built-in samples.</span>
      </div>
      <textarea id="ad-contract-input" class="ad-textarea" spellcheck="false" rows="24"></textarea>
    </section>

    <section class="ad-editor-pane">
      <div class="ad-editor-pane__header">
        <label for="ad-trace-input">Optional trace JSON</label>
        <span>Leave blank to preview contract-only coverage.</span>
      </div>
      <textarea id="ad-trace-input" class="ad-textarea" spellcheck="false" rows="24"></textarea>
    </section>
  </div>

  <section class="ad-results" aria-live="polite">
    <h2>Results</h2>
    <div id="ad-summary-output" class="ad-output-section"></div>
    <div id="ad-issues-output" class="ad-output-section"></div>
    <div id="ad-coverage-output" class="ad-output-section"></div>
    <div id="ad-patches-output" class="ad-output-section"></div>
    <div id="ad-regression-output" class="ad-output-section"></div>
    <div class="ad-output-section">
      <h3>Raw Report JSON</h3>
      <pre id="ad-report-json" class="ad-json-block" tabindex="0">Run Analyze to generate a report.</pre>
    </div>
  </section>
</div>

## First-Version Scope

The playground checks a small, deterministic subset of AgentDoctor concepts:

- contract field validation
- contract conflicts involving Markdown writing
- missing `no_write_on_missing_file` coverage
- traces that write after `pdf_reader` returns `file_not_found`
- forbidden tool calls
- parser-missed no-web-search restrictions
- simplified rule coverage preview

Patch previews and regression traces shown here are suggestions only. The page never applies patches and never modifies files.
