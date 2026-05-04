(function () {
  "use strict";

  if (typeof document === "undefined") {
    return;
  }

  var MISSING_FILE_RULE = {
    name: "no_write_on_missing_file",
    kind: "forbid_tool_after_tool_error",
    params: {
      tool: "markdown_writer",
      after_tool: "pdf_reader",
      error_status: "file_not_found"
    }
  };

  var MISSING_FILE_REGRESSION_TRACE = [
    {
      type: "tool_call",
      tool: "pdf_reader",
      args: { path: "missing.pdf" }
    },
    {
      type: "tool_result",
      tool: "pdf_reader",
      result: { status: "file_not_found" }
    },
    {
      type: "tool_call",
      tool: "markdown_writer",
      args: { path: "notes.md" }
    }
  ];

  var SAMPLES = {
    paper_reader_valid: {
      description: "A healthy trace: the agent reads a PDF successfully, then writes Markdown notes.",
      contract: {
        name: "paper_reader",
        goal: "Read a PDF paper and write Markdown notes.",
        tools: ["pdf_reader", "markdown_writer"],
        forbidden_tools: ["web_search"],
        rules: [clone(MISSING_FILE_RULE)]
      },
      trace: [
        {
          type: "tool_call",
          tool: "pdf_reader",
          args: { path: "paper.pdf" }
        },
        {
          type: "tool_result",
          tool: "pdf_reader",
          result: { status: "ok" }
        },
        {
          type: "tool_call",
          tool: "markdown_writer",
          args: { path: "notes.md" }
        }
      ]
    },
    missing_file_write: {
      description: "A missing PDF is reported, but the trace still writes notes. The contract also lacks the stop rule.",
      contract: {
        name: "paper_reader_missing_file_gap",
        goal: "Read a PDF paper and write Markdown notes.",
        tools: ["pdf_reader", "markdown_writer"],
        forbidden_tools: ["web_search"],
        rules: []
      },
      trace: clone(MISSING_FILE_REGRESSION_TRACE)
    },
    forbidden_web_search: {
      description: "The contract forbids web search, but the trace calls web_search anyway.",
      contract: {
        name: "offline_paper_reader",
        goal: "Read a supplied PDF and summarize it without external research.",
        tools: ["pdf_reader", "markdown_writer", "web_search"],
        forbidden_tools: ["web_search"],
        rules: [clone(MISSING_FILE_RULE)]
      },
      trace: [
        {
          type: "tool_call",
          tool: "pdf_reader",
          args: { path: "paper.pdf" }
        },
        {
          type: "tool_result",
          tool: "pdf_reader",
          result: { status: "ok" }
        },
        {
          type: "tool_call",
          tool: "web_search",
          args: { query: "paper title background" }
        }
      ]
    },
    contract_conflict_markdown: {
      description: "The goal asks for Markdown notes, but markdown_writer is globally forbidden.",
      contract: {
        name: "conflicted_paper_reader",
        goal: "Read a PDF paper and write Markdown notes.",
        tools: ["pdf_reader", "markdown_writer"],
        forbidden_tools: ["markdown_writer"],
        rules: []
      },
      trace: []
    },
    parser_missed_no_web: {
      description: "The original requirement bans web search, but the parsed contract forgot to forbid web_search.",
      contract: {
        name: "requirement_parser_preview",
        requirement_text: "Read the provided PDF and write concise Markdown notes. Do not use web search or any external network.",
        goal: "Read a PDF paper and write Markdown notes.",
        tools: ["pdf_reader", "markdown_writer", "web_search"],
        forbidden_tools: [],
        rules: [clone(MISSING_FILE_RULE)]
      },
      trace: [
        {
          type: "tool_call",
          tool: "pdf_reader",
          args: { path: "paper.pdf" }
        },
        {
          type: "tool_result",
          tool: "pdf_reader",
          result: { status: "ok" }
        },
        {
          type: "tool_call",
          tool: "markdown_writer",
          args: { path: "notes.md" }
        }
      ]
    }
  };

  var currentReport = null;

  document.addEventListener("DOMContentLoaded", initPlayground);

  function initPlayground() {
    var root = document.querySelector("[data-contract2agent-playground]");
    if (!root) {
      return;
    }

    var refs = {
      root: root,
      sample: document.getElementById("ad-sample-select"),
      sampleDescription: document.getElementById("ad-sample-description"),
      contract: document.getElementById("ad-contract-input"),
      trace: document.getElementById("ad-trace-input"),
      analyze: document.getElementById("ad-analyze-button"),
      reset: document.getElementById("ad-reset-button"),
      copy: document.getElementById("ad-copy-button"),
      clear: document.getElementById("ad-clear-button"),
      status: document.getElementById("ad-playground-status"),
      empty: document.getElementById("ad-empty-output"),
      summary: document.getElementById("ad-summary-output"),
      issues: document.getElementById("ad-issues-output"),
      coverage: document.getElementById("ad-coverage-output"),
      patches: document.getElementById("ad-patches-output"),
      regression: document.getElementById("ad-regression-output"),
      json: document.getElementById("ad-json-output")
    };

    if (!refs.sample || !refs.contract || !refs.trace || !refs.analyze) {
      return;
    }

    refs.sample.addEventListener("change", function () {
      loadSample(refs, refs.sample.value);
    });
    refs.analyze.addEventListener("click", function () {
      handleAnalyze(refs);
    });
    refs.reset.addEventListener("click", function () {
      loadSample(refs, refs.sample.value);
    });
    refs.copy.addEventListener("click", function () {
      copyReportJson(refs);
    });
    refs.clear.addEventListener("click", function () {
      clearInputs(refs);
    });

    loadSample(refs, refs.sample.value || "paper_reader_valid");
  }

  function loadSample(refs, sampleId) {
    var sample = getSamples()[sampleId] || getSamples().paper_reader_valid;
    refs.contract.value = stringifyJson(sample.contract);
    refs.trace.value = sample.trace && sample.trace.length ? stringifyJson(sample.trace) : "";
    if (refs.sampleDescription) {
      refs.sampleDescription.textContent = sample.description;
    }
    currentReport = null;
    setCopyEnabled(refs, false);
    renderEmpty(refs, "Sample loaded.", sample.description + " Click Analyze to preview the diagnosis.");
    setStatus(refs, sample.description + " Click Analyze.", "info");
  }

  function getSamples() {
    return SAMPLES;
  }

  function clearInputs(refs) {
    refs.contract.value = "";
    refs.trace.value = "";
    if (refs.sampleDescription) {
      refs.sampleDescription.textContent = "Paste your own JSON, or choose a sample scenario.";
    }
    currentReport = null;
    setCopyEnabled(refs, false);
    renderEmpty(refs, "Inputs cleared.", "Paste a contract JSON object, optionally add a trace, then click Analyze.");
    setStatus(refs, "Inputs cleared.", "info");
  }

  function handleAnalyze(refs) {
    setStatus(refs, "Analyzing the contract and trace in this browser...", "info");

    var contractResult = parseJsonInput("Contract", refs.contract.value, false);
    var traceResult = parseJsonInput("Trace", refs.trace.value, true);
    var errors = [contractResult.error, traceResult.error].filter(Boolean);

    if (errors.length) {
      currentReport = null;
      setCopyEnabled(refs, false);
      renderInputErrors(refs, errors);
      setStatus(refs, "Fix the JSON input and run Analyze again.", "error");
      return false;
    }

    var issues = analyzeContract(contractResult.value, traceResult.empty ? null : traceResult.value);
    var coverage = buildRuleCoveragePreview(contractResult.value, traceResult.empty ? null : traceResult.value);
    var report = buildReport(contractResult.value, issues, coverage);

    currentReport = report;
    setCopyEnabled(refs, true);
    renderReport(refs, report);
    setStatus(
      refs,
      report.total_issues
        ? "Analysis complete. " + report.total_issues + " issue(s) need review."
        : "Analysis complete. No issues detected in this preview.",
      report.total_issues ? "warning" : "success"
    );
    return true;
  }

  function parseJsonInput(label, text, allowEmpty) {
    var trimmed = String(text || "").trim();
    if (!trimmed) {
      if (allowEmpty) {
        return { ok: true, value: null, empty: true, error: null };
      }
      return { ok: false, value: null, empty: true, error: label + " JSON is required." };
    }

    try {
      var value = JSON.parse(trimmed);
      if (label === "Contract" && !isPlainObject(value)) {
        return { ok: false, value: null, empty: false, error: "Contract JSON must be an object." };
      }
      if (label === "Trace" && !Array.isArray(value) && !isTraceObject(value)) {
        return { ok: false, value: null, empty: false, error: "Trace JSON must be an array, or an object with an events array." };
      }
      return { ok: true, value: value, empty: false, error: null };
    } catch (error) {
      return { ok: false, value: null, empty: false, error: label + " JSON parse error: " + error.message };
    }
  }

  function analyzeContract(contract, trace) {
    return assignIssueIds(
      []
        .concat(validateContract(contract))
        .concat(detectContractConflicts(contract))
        .concat(detectMissingFileRuleGap(contract))
        .concat(detectTraceViolations(contract, trace))
        .concat(detectForbiddenToolViolations(contract, trace))
        .concat(detectParserMissedConstraints(contract))
        .concat(detectRuleCoverageGaps(contract, trace))
    );
  }

  function buildReport(contract, issues, coverage) {
    return {
      source: "contract2agent_playground",
      preview_scope: "static_browser_preview",
      contract_name: hasNonEmptyString(contract.name) ? contract.name.trim() : null,
      total_issues: issues.length,
      issue_counts_by_category: countBy(issues, "category"),
      issue_counts_by_affected_part: countBy(issues, "affected_agent_part"),
      issue_counts_by_severity: countBy(issues, "severity"),
      rule_coverage_summary: countBy(coverage, "status"),
      rule_coverage: coverage,
      issues: issues
    };
  }

  function validateContract(contract) {
    var issues = [];

    if (!hasNonEmptyString(contract.name)) {
      issues.push(buildIssue({
        severity: "warning",
        category: "contract_conflict",
        strictness: "ambiguous",
        affected_agent_part: "contract_consistency",
        summary: "Contract is missing a name.",
        natural_language_cause: "A stable contract name makes reports, baselines, and trace fixtures easier to compare.",
        evidence: { missing_field: "name" },
        confidence: 0.95,
        suggested_fix: "Add a short, stable name field to the contract."
      }));
    }

    if (!hasNonEmptyString(contract.goal)) {
      issues.push(buildIssue({
        severity: "warning",
        category: "contract_conflict",
        strictness: "ambiguous",
        affected_agent_part: "contract_consistency",
        summary: "Contract is missing a goal.",
        natural_language_cause: "Without a goal, Contract2Agent has less context for intent-level conflicts such as requiring notes while forbidding the writing tool.",
        evidence: { missing_field: "goal" },
        confidence: 0.9,
        suggested_fix: "Add a concise goal that states the expected agent outcome."
      }));
    }

    if (!Object.prototype.hasOwnProperty.call(contract, "tools")) {
      issues.push(buildIssue({
        severity: "warning",
        category: "contract_conflict",
        strictness: "ambiguous",
        affected_agent_part: "contract_consistency",
        summary: "Contract is missing tools.",
        natural_language_cause: "Tool declarations give the trace checker enough context to reason about allowed and forbidden calls.",
        evidence: { missing_field: "tools" },
        confidence: 0.95,
        suggested_fix: "Add a tools array listing the available tool names."
      }));
    } else if (!Array.isArray(contract.tools)) {
      issues.push(buildIssue({
        severity: "warning",
        category: "contract_conflict",
        strictness: "ambiguous",
        affected_agent_part: "contract_consistency",
        summary: "Contract tools field is not an array.",
        natural_language_cause: "The tools field should be an array so deterministic checks can compare declared tools against trace tool calls.",
        evidence: { field: "tools", observed_type: valueType(contract.tools) },
        confidence: 0.95,
        suggested_fix: "Change tools to an array, for example: \"tools\": [\"pdf_reader\", \"markdown_writer\"]."
      }));
    }

    if (Object.prototype.hasOwnProperty.call(contract, "forbidden_tools") && !Array.isArray(contract.forbidden_tools)) {
      issues.push(buildIssue({
        severity: "warning",
        category: "contract_conflict",
        strictness: "ambiguous",
        affected_agent_part: "contract_consistency",
        summary: "Contract forbidden_tools field is not an array.",
        natural_language_cause: "Forbidden tools need to be listed as an array so trace calls can be compared safely.",
        evidence: { field: "forbidden_tools", observed_type: valueType(contract.forbidden_tools) },
        confidence: 0.95,
        suggested_fix: "Change forbidden_tools to an array. Use an empty array when no tools are forbidden."
      }));
    }

    if (Object.prototype.hasOwnProperty.call(contract, "rules") && !Array.isArray(contract.rules)) {
      issues.push(buildIssue({
        severity: "warning",
        category: "contract_conflict",
        strictness: "ambiguous",
        affected_agent_part: "contract_consistency",
        summary: "Contract rules field is not an array.",
        natural_language_cause: "Rules should be an array so coverage and missing-rule checks can inspect each item.",
        evidence: { field: "rules", observed_type: valueType(contract.rules) },
        confidence: 0.95,
        suggested_fix: "Change rules to an array. Use an empty array when no rules are declared."
      }));
    }

    return issues;
  }

  function detectContractConflicts(contract) {
    var forbiddenTools = normalizedStringArray(contract.forbidden_tools);
    var goal = hasNonEmptyString(contract.goal) ? contract.goal : "";
    var mentionsWriting = /\b(markdown|notes?|write|writing|writer)\b/i.test(goal);

    if (!mentionsWriting || forbiddenTools.indexOf("markdown_writer") === -1) {
      return [];
    }

    return [
      buildIssue({
        severity: "error",
        category: "contract_conflict",
        strictness: "ambiguous",
        affected_agent_part: "contract_consistency",
        summary: "Goal requires Markdown writing, but markdown_writer is forbidden.",
        natural_language_cause: "The goal asks the agent to produce Markdown notes, while forbidden_tools blocks the only writing tool. The contract is internally inconsistent.",
        evidence: {
          goal: goal,
          forbidden_tools: stringArray(contract.forbidden_tools),
          matched_goal_terms: ["Markdown", "notes", "write"]
        },
        confidence: 0.9,
        suggested_fix: "Allow markdown_writer for successful reads, and forbid it only after pdf_reader returns file_not_found.",
        suggested_patch: {
          target: "agent_contract.yaml",
          type: "resolve_contract_conflict",
          remove_forbidden_tool: "markdown_writer",
          add_rule: clone(MISSING_FILE_RULE)
        }
      })
    ];
  }

  function detectMissingFileRuleGap(contract) {
    var tools = normalizedStringArray(contract.tools);
    var hasPdfReader = tools.indexOf("pdf_reader") !== -1;
    var hasMarkdownWriter = tools.indexOf("markdown_writer") !== -1;

    if (!hasPdfReader || !hasMarkdownWriter || hasNoWriteOnMissingFileRule(contract)) {
      return [];
    }

    return [
      buildIssue({
        severity: "warning",
        category: "contract_too_loose",
        strictness: "too_loose",
        affected_agent_part: "error_handling",
        summary: "Missing rule for writing after a missing PDF.",
        natural_language_cause: "The contract allows pdf_reader and markdown_writer, but does not include a rule equivalent to no_write_on_missing_file.",
        evidence: {
          tools: stringArray(contract.tools),
          required_rule: clone(MISSING_FILE_RULE)
        },
        confidence: 0.88,
        suggested_fix: "Add a rule forbidding markdown_writer after pdf_reader returns file_not_found.",
        suggested_patch: {
          target: "agent_contract.yaml",
          type: "add_rule",
          rule: clone(MISSING_FILE_RULE)
        },
        suggested_regression_trace: clone(MISSING_FILE_REGRESSION_TRACE)
      })
    ];
  }

  function detectTraceViolations(contract, trace) {
    var sequence = findFileNotFoundThenWrite(trace);
    if (!sequence) {
      return [];
    }

    var hasRule = hasNoWriteOnMissingFileRule(contract);
    return [
      buildIssue({
        severity: "error",
        category: hasRule ? "checker_too_loose" : "contract_too_loose",
        strictness: "too_loose",
        affected_agent_part: hasRule ? "trace_checker" : "error_handling",
        summary: "Trace writes after pdf_reader reports file_not_found.",
        natural_language_cause: hasRule
          ? "The contract contains no_write_on_missing_file, but this trace still reaches markdown_writer after a missing-file result. The checker or monitor should reject the sequence."
          : "The trace shows pdf_reader returning file_not_found followed by markdown_writer, and the contract lacks the rule that would forbid that sequence.",
        evidence: {
          matched_steps: sequence.matched_steps,
          file_not_found_event: sequence.file_not_found_event,
          write_event: sequence.write_event
        },
        confidence: 0.95,
        suggested_fix: hasRule
          ? "Ensure the trace checker and runtime monitor enforce no_write_on_missing_file."
          : "Add no_write_on_missing_file and use this trace as a negative regression case.",
        suggested_patch: hasRule
          ? {
              target: "contract2agent/checker.py",
              type: "enforce_rule",
              description: "Reject traces where markdown_writer follows pdf_reader file_not_found."
            }
          : {
              target: "agent_contract.yaml",
              type: "add_rule",
              rule: clone(MISSING_FILE_RULE)
            },
        suggested_regression_trace: clone(MISSING_FILE_REGRESSION_TRACE)
      })
    ];
  }

  function detectForbiddenToolViolations(contract, trace) {
    var forbiddenTools = uniqueStrings(normalizedStringArray(contract.forbidden_tools));
    if (!forbiddenTools.length || !trace) {
      return [];
    }

    var issues = [];
    forbiddenTools.forEach(function (tool) {
      var calls = findToolCalls(trace, tool);
      if (!calls.length) {
        return;
      }

      issues.push(buildIssue({
        severity: "error",
        category: "agent_behavior_failure",
        strictness: "not_applicable",
        affected_agent_part: tool === "web_search" ? "forbidden_tool_control" : "capability_scope",
        summary: "Trace calls forbidden tool " + tool + ".",
        natural_language_cause: "The contract forbids " + tool + ", but the trace contains one or more tool_call events for that tool.",
        evidence: {
          forbidden_tool: tool,
          matched_steps: calls.map(function (call) { return call.index; }),
          calls: calls.map(function (call) { return call.event; })
        },
        confidence: 0.96,
        suggested_fix: "Keep the forbidden tool in the contract, then check the agent prompt, checker, and runtime monitor for enforcement gaps.",
        suggested_patch: {
          target: "agent_contract.yaml",
          type: "confirm_forbidden_tool",
          forbidden_tool: tool,
          description: "Ensure forbidden_tools includes " + tool + " and add a negative trace that calls it."
        },
        suggested_regression_trace: [
          {
            type: "tool_call",
            tool: tool,
            args: tool === "web_search" ? { query: "external background" } : {}
          }
        ]
      }));
    });

    return issues;
  }

  function detectParserMissedConstraints(contract) {
    var requirement = requirementText(contract);
    var matchedRestriction = noWebSearchRestriction(requirement.text);
    var forbiddenTools = normalizedStringArray(contract.forbidden_tools);
    var declaredTools = normalizedStringArray(contract.tools);

    if (!matchedRestriction || forbiddenTools.indexOf("web_search") !== -1) {
      return [];
    }

    return [
      buildIssue({
        severity: "error",
        category: "parser_missed_constraint",
        strictness: "too_loose",
        affected_agent_part: "contract_parser",
        summary: "Requirement bans web search, but the contract does not forbid web_search.",
        natural_language_cause: "The source requirement contains a no-web-search restriction, but forbidden_tools omits web_search. The parsed contract is looser than the user instruction.",
        evidence: {
          matched_restriction: matchedRestriction,
          requirement_fields: requirement.fields,
          tools_include_web_search: declaredTools.indexOf("web_search") !== -1,
          forbidden_tools: stringArray(contract.forbidden_tools)
        },
        confidence: 0.92,
        suggested_fix: "Add web_search to forbidden_tools and add a negative trace that calls web_search.",
        suggested_patch: {
          target: "agent_contract.yaml",
          type: "add_forbidden_tool",
          forbidden_tool: "web_search"
        },
        suggested_regression_trace: [
          {
            type: "tool_call",
            tool: "web_search",
            args: { query: "paper background" }
          }
        ]
      })
    ];
  }

  function detectRuleCoverageGaps(contract, trace) {
    var coverage = buildRuleCoveragePreview(contract, trace);
    return coverage
      .filter(function (item) {
        return item.status === "uncovered";
      })
      .map(function (item) {
        return buildIssue({
          severity: "info",
          category: "rule_uncovered",
          strictness: "not_applicable",
          affected_agent_part: "rule_coverage",
          summary: "Rule lacks trace coverage: " + item.rule_name + ".",
          natural_language_cause: item.uncovered_reason || "No trace in this preview exercises the rule.",
          evidence: {
            rule_name: item.rule_name,
            rule_kind: item.rule_kind,
            coverage_status: item.status
          },
          confidence: 0.78,
          suggested_fix: item.suggested_test
            ? "Add a focused trace for " + item.rule_name + "."
            : "Add positive and negative traces that exercise this rule.",
          suggested_regression_trace: item.suggested_test && item.suggested_test.trace
            ? item.suggested_test.trace
            : null
        });
      });
  }

  function buildRuleCoveragePreview(contract, trace) {
    var coverage = [];
    var rules = Array.isArray(contract.rules) ? contract.rules : [];
    var traceProvided = traceEvents(trace).length > 0;
    var positiveSequence = findSuccessfulReadThenWrite(trace);
    var negativeSequence = findFileNotFoundThenWrite(trace);

    rules.forEach(function (rule, index) {
      var ruleName = hasNonEmptyString(rule.name) ? rule.name : "unnamed_rule_" + String(index + 1);
      var ruleKind = hasNonEmptyString(rule.kind) ? rule.kind : "unknown";

      if (isNoWriteOnMissingFileRule(rule)) {
        var hasPositive = Boolean(positiveSequence);
        var hasNegative = Boolean(negativeSequence);
        coverage.push({
          rule_name: ruleName,
          rule_kind: ruleKind,
          has_positive_trace: hasPositive,
          has_negative_trace: hasNegative,
          status: coverageStatus(traceProvided, hasPositive, hasNegative),
          covered_by: hasPositive || hasNegative ? ["playground_trace"] : [],
          uncovered_reason: hasPositive || hasNegative ? null : "No trace path exercises no_write_on_missing_file.",
          suggested_test: hasNegative ? null : { trace: clone(MISSING_FILE_REGRESSION_TRACE) }
        });
        return;
      }

      coverage.push({
        rule_name: ruleName,
        rule_kind: ruleKind,
        has_positive_trace: false,
        has_negative_trace: false,
        status: traceProvided ? "unknown" : "uncovered",
        covered_by: [],
        uncovered_reason: traceProvided
          ? "The static playground does not implement coverage logic for this rule kind."
          : "No trace was provided."
      });
    });

    uniqueStrings(normalizedStringArray(contract.forbidden_tools)).forEach(function (tool) {
      var calls = findToolCalls(trace, tool);
      var hasNegative = calls.length > 0;
      coverage.push({
        rule_name: "forbidden_tool:" + tool,
        rule_kind: "forbidden_tool",
        has_positive_trace: false,
        has_negative_trace: hasNegative,
        status: hasNegative ? "weak" : traceProvided ? "unknown" : "uncovered",
        covered_by: hasNegative ? ["playground_trace"] : [],
        uncovered_reason: hasNegative ? null : "No negative trace calls " + tool + ".",
        suggested_test: hasNegative ? null : {
          trace: [
            {
              type: "tool_call",
              tool: tool,
              args: {}
            }
          ]
        }
      });
    });

    return coverage;
  }

  function coverageStatus(traceProvided, hasPositive, hasNegative) {
    if (!traceProvided) {
      return "uncovered";
    }
    if (hasPositive && hasNegative) {
      return "ok";
    }
    if (hasPositive || hasNegative) {
      return "weak";
    }
    return "uncovered";
  }

  function buildIssue(fields) {
    return {
      id: "pending",
      severity: fields.severity || "warning",
      category: fields.category || "agent_behavior_failure",
      strictness: fields.strictness || "not_applicable",
      affected_agent_part: fields.affected_agent_part || "capability_scope",
      summary: fields.summary || "Playground issue detected.",
      natural_language_cause: fields.natural_language_cause || fields.summary || "A deterministic playground check matched.",
      evidence: fields.evidence || {},
      confidence: typeof fields.confidence === "number" ? fields.confidence : 0.75,
      suggested_fix: fields.suggested_fix || null,
      suggested_patch: fields.suggested_patch || null,
      suggested_regression_trace: fields.suggested_regression_trace || null
    };
  }

  function assignIssueIds(issues) {
    return issues.map(function (issue, index) {
      var nextIssue = Object.assign({}, issue);
      nextIssue.id = "ATD" + String(index + 1).padStart(3, "0");
      return nextIssue;
    });
  }

  function renderReport(refs, report) {
    hideEmpty(refs);
    renderSummary(refs.summary, report);
    renderIssues(refs.issues, report.issues);
    renderCoverageTable(refs.coverage, report.rule_coverage);
    renderPatchPreviews(refs.patches, report.issues);
    renderRegressionTraces(refs.regression, report.issues);
    renderJsonPreview(refs.json, report);
  }

  function renderEmpty(refs, title, message) {
    clearOutputSections(refs);
    if (refs.empty) {
      refs.empty.hidden = false;
      refs.empty.replaceChildren(el("strong", "", title), el("span", "", message));
    }
  }

  function hideEmpty(refs) {
    if (refs.empty) {
      refs.empty.hidden = true;
    }
  }

  function renderInputErrors(refs, errors) {
    hideEmpty(refs);
    clearOutputSections(refs);
    var section = createSection("Input Error");
    errors.forEach(function (message) {
      section.appendChild(el("p", "ad-error-text", message));
    });
    refs.summary.replaceChildren(section);
  }

  function renderSummary(container, report) {
    container.replaceChildren();
    var section = createSection("Summary");
    var grid = el("div", "ad-summary-grid");
    var severityCounts = report.issue_counts_by_severity || {};

    grid.appendChild(summaryCard("Total issues", report.total_issues));
    grid.appendChild(summaryCard("Errors", severityCounts.error || 0));
    grid.appendChild(summaryCard("Warnings", severityCounts.warning || 0));
    grid.appendChild(summaryCard("Coverage items", report.rule_coverage.length));
    section.appendChild(grid);

    if (report.total_issues === 0) {
      var noIssues = el("div", "ad-callout ad-callout--success");
      noIssues.appendChild(el("strong", "", "No issues detected in this browser-side preview."));
      noIssues.appendChild(el("span", "", "The full CLI can run deeper checks, write reports, and generate regression trace files."));
      section.appendChild(noIssues);
    } else {
      section.appendChild(countList("Issue categories", report.issue_counts_by_category));
    }

    container.appendChild(section);
  }

  function renderIssues(container, issues) {
    container.replaceChildren();
    var section = createSection("Issues");

    if (!issues.length) {
      section.appendChild(el("p", "ad-empty", "No issue cards for this report."));
      container.appendChild(section);
      return;
    }

    issues.forEach(function (issue) {
      section.appendChild(renderIssueCard(issue));
    });
    container.appendChild(section);
  }

  function renderIssueCard(issue) {
    var card = el("article", "ad-issue-card ad-issue-card--" + safeClass(issue.severity));
    var header = el("div", "ad-issue-card__header");
    var titleBlock = el("div", "ad-issue-card__title");
    titleBlock.appendChild(el("span", "ad-issue-id", issue.id));
    titleBlock.appendChild(el("h4", "", issue.summary));

    var badges = el("div", "ad-badge-row");
    badges.appendChild(badge(issue.severity, "severity"));
    badges.appendChild(badge(issue.category, "category"));
    badges.appendChild(badge(issue.strictness, "strictness"));
    badges.appendChild(badge(issue.affected_agent_part, "part"));

    header.appendChild(titleBlock);
    header.appendChild(badges);
    card.appendChild(header);
    card.appendChild(labeledText("Cause", issue.natural_language_cause));

    if (issue.suggested_fix) {
      card.appendChild(labeledText("Suggested fix", issue.suggested_fix));
    }

    card.appendChild(labeledText("Confidence", Math.round(issue.confidence * 100) + "%"));
    card.appendChild(detailsBlock("Evidence", issue.evidence));

    if (issue.suggested_patch) {
      card.appendChild(detailsBlock("Suggested patch preview", issue.suggested_patch));
    }

    if (issue.suggested_regression_trace) {
      card.appendChild(detailsBlock("Suggested regression trace", issue.suggested_regression_trace));
    }

    return card;
  }

  function renderCoverageTable(container, coverage) {
    container.replaceChildren();
    var section = createSection("Rule Coverage");

    if (!coverage.length) {
      section.appendChild(el("p", "ad-empty", "No declared rules or forbidden tools to preview."));
      container.appendChild(section);
      return;
    }

    var wrapper = el("div", "ad-table-wrap");
    var table = document.createElement("table");
    table.className = "ad-coverage-table";
    var thead = document.createElement("thead");
    var headerRow = document.createElement("tr");
    ["Rule", "Kind", "Positive", "Negative", "Status"].forEach(function (label) {
      headerRow.appendChild(el("th", "", label));
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    var tbody = document.createElement("tbody");
    coverage.forEach(function (item) {
      var row = document.createElement("tr");
      row.appendChild(el("td", "", item.rule_name));
      row.appendChild(el("td", "", item.rule_kind || "unknown"));
      row.appendChild(el("td", "", item.has_positive_trace ? "yes" : "no"));
      row.appendChild(el("td", "", item.has_negative_trace ? "yes" : "no"));
      var statusCell = document.createElement("td");
      statusCell.appendChild(badge(item.status, "status"));
      row.appendChild(statusCell);
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    wrapper.appendChild(table);
    section.appendChild(wrapper);
    container.appendChild(section);
  }

  function renderPatchPreviews(container, issues) {
    container.replaceChildren();
    var section = createSection("Suggested Patches");
    var patchIssues = issues.filter(function (issue) {
      return issue.suggested_patch;
    });

    if (!patchIssues.length) {
      section.appendChild(el("p", "ad-empty", "No patch previews for this report."));
      container.appendChild(section);
      return;
    }

    patchIssues.forEach(function (issue) {
      var card = el("article", "ad-preview-card");
      card.appendChild(el("h4", "", issue.id + " " + issue.summary));
      card.appendChild(detailsBlock("Patch JSON", issue.suggested_patch, true));
      section.appendChild(card);
    });

    container.appendChild(section);
  }

  function renderRegressionTraces(container, issues) {
    container.replaceChildren();
    var section = createSection("Regression Traces");
    var traceIssues = issues.filter(function (issue) {
      return issue.suggested_regression_trace;
    });

    if (!traceIssues.length) {
      section.appendChild(el("p", "ad-empty", "No regression trace previews for this report."));
      container.appendChild(section);
      return;
    }

    traceIssues.forEach(function (issue) {
      var card = el("article", "ad-preview-card");
      card.appendChild(el("h4", "", issue.id + " " + issue.summary));
      card.appendChild(detailsBlock("Trace JSON", issue.suggested_regression_trace, true));
      section.appendChild(card);
    });

    container.appendChild(section);
  }

  function renderJsonPreview(container, report) {
    container.replaceChildren();
    var section = createSection("Report JSON");
    section.appendChild(detailsBlock("Raw report", report));
    container.appendChild(section);
  }

  function clearOutputSections(refs) {
    [refs.summary, refs.issues, refs.coverage, refs.patches, refs.regression, refs.json].forEach(function (node) {
      if (node) {
        node.replaceChildren();
      }
    });
  }

  function copyReportJson(refs) {
    if (!currentReport) {
      setStatus(refs, "Run Analyze before copying a report.", "error");
      return;
    }

    var text = stringifyJson(currentReport);
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () {
        setStatus(refs, "Copied. Report JSON is on your clipboard.", "success");
      }).catch(function () {
        fallbackCopy(text, refs);
      });
      return;
    }

    fallbackCopy(text, refs);
  }

  function fallbackCopy(text, refs) {
    var buffer = document.createElement("textarea");
    buffer.value = text;
    buffer.setAttribute("readonly", "");
    buffer.className = "ad-copy-buffer";
    document.body.appendChild(buffer);
    buffer.select();

    var copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (error) {
      copied = false;
    }

    document.body.removeChild(buffer);
    setStatus(
      refs,
      copied ? "Copied. Report JSON is on your clipboard." : "Unable to copy. Select the raw JSON block and copy manually.",
      copied ? "success" : "error"
    );
  }

  function hasNoWriteOnMissingFileRule(contract) {
    var rules = Array.isArray(contract.rules) ? contract.rules : [];
    return rules.some(isNoWriteOnMissingFileRule);
  }

  function isNoWriteOnMissingFileRule(rule) {
    if (!isPlainObject(rule)) {
      return false;
    }
    var params = isPlainObject(rule.params) ? rule.params : {};
    return normalize(rule.kind) === "forbid_tool_after_tool_error"
      && normalize(params.tool) === "markdown_writer"
      && normalize(params.after_tool) === "pdf_reader"
      && normalize(params.error_status) === "file_not_found";
  }

  function findFileNotFoundThenWrite(trace) {
    var events = traceEvents(trace);
    for (var index = 0; index < events.length; index += 1) {
      var event = events[index];
      if (!isToolResult(event, "pdf_reader") || normalize(eventStatus(event)) !== "file_not_found") {
        continue;
      }
      for (var next = index + 1; next < events.length; next += 1) {
        var candidate = events[next];
        if (isToolCall(candidate, "markdown_writer")) {
          return {
            matched_steps: [index, next],
            file_not_found_event: event,
            write_event: candidate
          };
        }
      }
    }
    return null;
  }

  function findSuccessfulReadThenWrite(trace) {
    var events = traceEvents(trace);
    for (var index = 0; index < events.length; index += 1) {
      var event = events[index];
      if (!isToolResult(event, "pdf_reader") || ["ok", "success", "passed"].indexOf(normalize(eventStatus(event))) === -1) {
        continue;
      }
      for (var next = index + 1; next < events.length; next += 1) {
        if (isToolCall(events[next], "markdown_writer")) {
          return {
            matched_steps: [index, next],
            read_event: event,
            write_event: events[next]
          };
        }
      }
    }
    return null;
  }

  function findToolCalls(trace, tool) {
    var calls = [];
    traceEvents(trace).forEach(function (event, index) {
      if (isToolCall(event, tool)) {
        calls.push({ index: index, event: event });
      }
    });
    return calls;
  }

  function traceEvents(trace) {
    if (!trace) {
      return [];
    }
    if (Array.isArray(trace)) {
      return trace.filter(isPlainObject);
    }
    if (isTraceObject(trace)) {
      return trace.events.filter(isPlainObject);
    }
    return [];
  }

  function isTraceObject(value) {
    return isPlainObject(value) && Array.isArray(value.events);
  }

  function isToolCall(event, tool) {
    return isPlainObject(event) && event.type === "tool_call" && normalize(event.tool) === normalize(tool);
  }

  function isToolResult(event, tool) {
    return isPlainObject(event) && event.type === "tool_result" && normalize(event.tool) === normalize(tool);
  }

  function eventStatus(event) {
    if (!isPlainObject(event)) {
      return "";
    }
    if (hasNonEmptyString(event.status)) {
      return event.status;
    }
    if (isPlainObject(event.result) && hasNonEmptyString(event.result.status)) {
      return event.result.status;
    }
    if (hasNonEmptyString(event.result)) {
      return event.result;
    }
    return "";
  }

  function requirementText(contract) {
    var fields = ["requirement", "requirement_text", "user_requirement", "original_requirement"];
    var chunks = [];
    var matchedFields = [];
    fields.forEach(function (field) {
      if (hasNonEmptyString(contract[field])) {
        matchedFields.push(field);
        chunks.push(contract[field]);
      }
    });
    return {
      text: chunks.join("\n"),
      fields: matchedFields
    };
  }

  function noWebSearchRestriction(text) {
    var patterns = [
      /\bno\s+web\s+search\b/i,
      /\bdo\s+not\s+use\s+web\s+search\b/i,
      /\bnever\s+use\s+(?:the\s+)?browser\b/i,
      /\bno\s+external\s+network\b/i,
      /\bdo\s+not\s+use\s+(?:the\s+)?external\s+network\b/i,
      /\bwithout\s+(?:any\s+)?external\s+network\b/i
    ];
    for (var index = 0; index < patterns.length; index += 1) {
      var match = String(text || "").match(patterns[index]);
      if (match) {
        return match[0];
      }
    }
    return "";
  }

  function countBy(items, key) {
    var counts = {};
    items.forEach(function (item) {
      var value = item[key] || "unknown";
      counts[value] = (counts[value] || 0) + 1;
    });
    return counts;
  }

  function normalizedStringArray(value) {
    return stringArray(value).map(normalize).filter(Boolean);
  }

  function stringArray(value) {
    if (!Array.isArray(value)) {
      return [];
    }
    return value.map(function (item) {
      return String(item);
    });
  }

  function uniqueStrings(items) {
    var seen = {};
    var result = [];
    items.forEach(function (item) {
      if (!item || seen[item]) {
        return;
      }
      seen[item] = true;
      result.push(item);
    });
    return result;
  }

  function normalize(value) {
    return String(value || "").trim().toLowerCase();
  }

  function hasNonEmptyString(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function valueType(value) {
    if (Array.isArray(value)) {
      return "array";
    }
    if (value === null) {
      return "null";
    }
    return typeof value;
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function stringifyJson(value) {
    return JSON.stringify(value, null, 2);
  }

  function createSection(title) {
    var section = el("section", "ad-card-section");
    section.appendChild(el("h3", "", title));
    return section;
  }

  function summaryCard(label, value) {
    var card = el("div", "ad-summary-card");
    card.appendChild(el("span", "ad-summary-card__label", label));
    card.appendChild(el("strong", "ad-summary-card__value", String(value)));
    return card;
  }

  function countList(title, counts) {
    var wrapper = el("div", "ad-count-list");
    wrapper.appendChild(el("h4", "", title));
    var list = document.createElement("ul");
    Object.keys(counts).sort().forEach(function (key) {
      var item = document.createElement("li");
      item.appendChild(el("span", "", key));
      item.appendChild(el("strong", "", String(counts[key])));
      list.appendChild(item);
    });
    wrapper.appendChild(list);
    return wrapper;
  }

  function labeledText(label, value) {
    var wrapper = el("div", "ad-labeled");
    wrapper.appendChild(el("span", "ad-labeled__label", label));
    wrapper.appendChild(el("p", "ad-labeled__text", value));
    return wrapper;
  }

  function detailsBlock(label, value, open) {
    var details = document.createElement("details");
    details.className = "ad-details";
    if (open) {
      details.open = true;
    }
    details.appendChild(el("summary", "", label));
    details.appendChild(renderJsonBlock(value));
    return details;
  }

  function renderJsonBlock(value) {
    var pre = document.createElement("pre");
    pre.className = "ad-json-block";
    pre.tabIndex = 0;
    pre.textContent = stringifyJson(value);
    return pre;
  }

  function badge(value, kind) {
    return el("span", "ad-badge ad-badge--" + safeClass(kind) + " ad-badge--" + safeClass(value), value);
  }

  function safeClass(value) {
    return normalize(value).replace(/[^a-z0-9_-]/g, "_");
  }

  function el(tagName, className, text) {
    var node = document.createElement(tagName);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = String(text);
    }
    return node;
  }

  function setCopyEnabled(refs, enabled) {
    if (refs.copy) {
      refs.copy.disabled = !enabled;
    }
  }

  function setStatus(refs, message, level) {
    if (!refs.status) {
      return;
    }
    refs.status.className = "ad-status ad-status--" + safeClass(level || "info");
    refs.status.textContent = message;
  }
}());
