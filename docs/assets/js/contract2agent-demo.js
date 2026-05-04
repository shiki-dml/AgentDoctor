(function () {
  "use strict";

  var STORAGE_KEY = "contract2agent.demo.config";
  var DEFAULT_EXAMPLE = "high_risk_combined";
  var currentReport = null;

  document.addEventListener("DOMContentLoaded", initDemo);

  function initDemo() {
    var elements = getDemoElements();
    if (!elements.root) {
      return;
    }

    var savedInput = loadInputFromLocalStorage();
    if (savedInput) {
      elements.input.value = savedInput;
      updateInputStatus(elements);
    } else {
      loadExample(elements, DEFAULT_EXAMPLE);
    }

    elements.loadExample.addEventListener("click", function () {
      loadExample(elements, elements.exampleSelect.value);
    });
    elements.diagnose.addEventListener("click", function () {
      diagnoseFromInput(elements);
    });
    elements.formatJson.addEventListener("click", function () {
      formatJsonInput(elements);
    });
    elements.clear.addEventListener("click", function () {
      clearInput(elements);
    });
    elements.reset.addEventListener("click", function () {
      elements.exampleSelect.value = DEFAULT_EXAMPLE;
      loadExample(elements, DEFAULT_EXAMPLE);
    });
    elements.input.addEventListener("keydown", function (event) {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        diagnoseFromInput(elements);
      }
    });
    elements.input.addEventListener("input", function () {
      saveInputToLocalStorage(elements.input.value);
      updateInputStatus(elements);
      clearReport(elements, "Input changed. Run diagnosis to refresh the report.");
    });
    elements.copyJson.addEventListener("click", function () {
      if (currentReport) {
        copyToClipboard(JSON.stringify(currentReport, null, 2), elements, "JSON report copied.");
      }
    });
    elements.copyPatch.addEventListener("click", function () {
      if (currentReport) {
        copyToClipboard(JSON.stringify(currentReport.minimal_patch || {}, null, 2), elements, "Minimal patch copied.");
      }
    });
    elements.downloadJson.addEventListener("click", function () {
      if (currentReport) {
        downloadTextFile("contract2agent-demo-report.json", JSON.stringify(currentReport, null, 2), "application/json");
        setReportStatus(elements, "JSON report download started.", "success");
      }
    });
    elements.downloadMarkdown.addEventListener("click", function () {
      if (currentReport) {
        downloadTextFile("contract2agent-demo-report.md", buildMarkdownReport(currentReport), "text/markdown");
        setReportStatus(elements, "Markdown report download started.", "success");
      }
    });
  }

  function getDemoElements() {
    return {
      root: document.querySelector("[data-contract2agent-demo]"),
      input: document.getElementById("c2a-demo-config-input"),
      inputStatus: document.getElementById("c2a-demo-input-status"),
      reportStatus: document.getElementById("c2a-demo-report-status"),
      reportOutput: document.getElementById("c2a-demo-report-output"),
      exampleSelect: document.getElementById("c2a-demo-example-select"),
      loadExample: document.getElementById("c2a-demo-load-example"),
      diagnose: document.getElementById("c2a-demo-diagnose"),
      formatJson: document.getElementById("c2a-demo-format-json"),
      clear: document.getElementById("c2a-demo-clear"),
      reset: document.getElementById("c2a-demo-reset"),
      copyJson: document.getElementById("c2a-demo-copy-json"),
      copyPatch: document.getElementById("c2a-demo-copy-patch"),
      downloadJson: document.getElementById("c2a-demo-download-json"),
      downloadMarkdown: document.getElementById("c2a-demo-download-md")
    };
  }

  function getExamples() {
    return {
      valid_minimal_agent: {
        agent_name: "DocsAnswerAgent",
        tools: ["search_docs"],
        routing: {
          fallback: "human_review"
        },
        memory: {
          enabled: false
        },
        budget: {
          max_tokens: 50000
        },
        output_schema: {
          type: "object",
          required: ["answer"],
          properties: {
            answer: {
              type: "string"
            }
          }
        },
        evaluation: {
          enabled: true,
          min_pass_rate: 0.95
        }
      },
      missing_tools: {
        agent_name: "ToolGapAgent",
        tools: [],
        routing: {
          fallback: "human_review"
        },
        memory: {
          enabled: false
        },
        budget: {
          max_tokens: 50000
        },
        output_schema: {
          type: "object",
          required: ["answer"],
          properties: {
            answer: {
              type: "string"
            }
          }
        },
        evaluation: {
          enabled: true,
          min_pass_rate: 0.95
        }
      },
      missing_fallback_route: {
        agent_name: "RoutingGapAgent",
        tools: ["search_docs"],
        routing: {},
        memory: {
          enabled: false
        },
        budget: {
          max_tokens: 50000
        },
        output_schema: {
          type: "object",
          required: ["answer"],
          properties: {
            answer: {
              type: "string"
            }
          }
        },
        evaluation: {
          enabled: true,
          min_pass_rate: 0.95
        }
      },
      unsafe_memory_retention: {
        agent_name: "MemoryHeavyAgent",
        tools: ["search_docs"],
        routing: {
          fallback: "human_review"
        },
        memory: {
          enabled: true,
          retention_days: 365
        },
        budget: {
          max_tokens: 50000
        },
        output_schema: {
          type: "object",
          required: ["answer"],
          properties: {
            answer: {
              type: "string"
            }
          }
        },
        evaluation: {
          enabled: true,
          min_pass_rate: 0.95
        }
      },
      excessive_token_budget: {
        agent_name: "BudgetRiskAgent",
        tools: ["search_docs"],
        routing: {
          fallback: "human_review"
        },
        memory: {
          enabled: false
        },
        budget: {
          max_tokens: 200000
        },
        output_schema: {
          type: "object",
          required: ["answer"],
          properties: {
            answer: {
              type: "string"
            }
          }
        },
        evaluation: {
          enabled: true,
          min_pass_rate: 0.95
        }
      },
      missing_output_schema: {
        agent_name: "SchemaGapAgent",
        tools: ["search_docs"],
        routing: {
          fallback: "human_review"
        },
        memory: {
          enabled: false
        },
        budget: {
          max_tokens: 50000
        },
        evaluation: {
          enabled: true,
          min_pass_rate: 0.95
        }
      },
      high_risk_combined: {
        name: "",
        description: "A deliberately incomplete deployment profile for browser-side diagnosis.",
        tools: [],
        routing: {
          primary: "autonomous"
        },
        memory: {
          enabled: true,
          retention_days: 365
        },
        budget: {
          max_tokens: 250000
        }
      }
    };
  }

  function loadExample(elements, name) {
    var examples = getExamples();
    var config = examples[name] || examples[DEFAULT_EXAMPLE];
    elements.input.value = stringify(config);
    saveInputToLocalStorage(elements.input.value);
    currentReport = null;
    updateInputStatus(elements);
    clearReport(elements, "Example loaded. Click Diagnose to generate a report.");
  }

  function parseConfig(text) {
    var trimmed = String(text || "").trim();
    if (!trimmed) {
      return {
        ok: false,
        error: "Configuration JSON is required."
      };
    }
    try {
      var value = JSON.parse(trimmed);
      if (!isPlainObject(value)) {
        return {
          ok: false,
          error: "Configuration must be a JSON object."
        };
      }
      return {
        ok: true,
        value: value
      };
    } catch (error) {
      return {
        ok: false,
        error: "JSON parse error: " + error.message
      };
    }
  }

  function diagnoseFromInput(elements) {
    var parsed = parseConfig(elements.input.value);
    if (!parsed.ok) {
      renderError(elements, parsed.error);
      return;
    }
    var report = diagnoseConfig(parsed.value);
    currentReport = report;
    renderReport(elements, report);
    setInputStatus(elements, "Valid JSON.", "success");
    setReportStatus(elements, "Diagnosis complete.", report.status === "pass" ? "success" : report.status);
    setReportActionsEnabled(elements, true);
  }

  function diagnoseConfig(config) {
    var ruleResult = runRules(config);
    var riskScore = computeRiskScore(ruleResult.failures);
    var severity = deriveSeverity(riskScore);
    var status = deriveStatus(riskScore);
    var minimalPatch = buildMinimalPatch(ruleResult.failures);
    var estimatedEffort = estimateEffort(ruleResult.failures);
    var regressionTrace = buildRegressionTrace(ruleResult.coverage);
    var suggestedFixes = ruleResult.failures.map(function (failure) {
      return {
        id: failure.id,
        title: failure.title,
        suggested_fix: failure.suggested_fix
      };
    });

    regressionTrace.push("Generated minimal patch preview.");
    regressionTrace.push("Computed final risk score and severity.");

    return {
      project: "Contract2Agent",
      demo_mode: true,
      status: status,
      severity: severity,
      risk_score: riskScore,
      summary: {
        total_rules: ruleResult.coverage.length,
        passed_rules: ruleResult.coverage.filter(function (item) { return item.status === "pass"; }).length,
        failed_rules: ruleResult.failures.length,
        patch_available: Object.keys(minimalPatch).length > 0
      },
      failure_types: ruleResult.failures.map(toFailureType),
      suggested_fixes: suggestedFixes,
      minimal_patch: minimalPatch,
      estimated_effort: estimatedEffort,
      regression_trace: regressionTrace,
      rule_coverage: ruleResult.coverage
    };
  }

  function runRules(config) {
    var coverage = [];
    var failures = [];

    addRuleResult(
      coverage,
      failures,
      checkAgentIdentity(config)
    );
    addRuleResult(
      coverage,
      failures,
      checkToolsAvailable(config)
    );
    addRuleResult(
      coverage,
      failures,
      checkFallbackRoute(config)
    );
    addRuleResult(
      coverage,
      failures,
      checkMemoryRetention(config)
    );
    addRuleResult(
      coverage,
      failures,
      checkTokenBudget(config)
    );
    addRuleResult(
      coverage,
      failures,
      checkOutputSchema(config)
    );
    addRuleResult(
      coverage,
      failures,
      checkEvaluationPolicy(config)
    );

    var accumulatedRisk = computeRiskScore(failures);
    addRuleResult(
      coverage,
      failures,
      checkHumanReviewGate(config, accumulatedRisk)
    );

    return {
      coverage: coverage,
      failures: failures
    };
  }

  function addRuleResult(coverage, failures, result) {
    coverage.push({
      rule_id: result.rule_id,
      title: result.title,
      status: result.status,
      severity: result.severity,
      detail: result.detail
    });
    if (result.status === "fail" || result.status === "warn") {
      failures.push({
        id: result.failure_id,
        rule_id: result.rule_id,
        title: result.failure_title,
        severity: result.severity,
        risk_weight: result.risk_weight,
        description: result.description,
        why_it_matters: result.why_it_matters,
        suggested_fix: result.suggested_fix,
        patch: result.patch,
        affected_area: result.affected_area
      });
    }
  }

  function checkAgentIdentity(config) {
    var ok = hasText(config.agent_name) || hasText(config.name);
    return ruleResult({
      rule_id: "agent_identity_present",
      title: "Agent identity present",
      status: ok ? "pass" : "fail",
      severity: "medium",
      detail: ok ? "agent_name or name is present" : "agent_name or name is missing",
      failure_id: "missing_agent_identity",
      failure_title: "Missing agent identity",
      risk_weight: 0.10,
      description: "No stable agent identity was declared.",
      why_it_matters: "Reports, baselines, and regression comparisons need a stable identity to connect findings to the right agent.",
      suggested_fix: "Add a stable agent_name field.",
      patch: {
        agent_name: "ExampleAgent"
      },
      affected_area: "identity"
    });
  }

  function checkToolsAvailable(config) {
    var ok = Array.isArray(config.tools) && config.tools.length > 0;
    return ruleResult({
      rule_id: "tools_available",
      title: "Tools available",
      status: ok ? "pass" : "fail",
      severity: "high",
      detail: ok ? "tools contains at least one item" : "tools is missing, not an array, or empty",
      failure_id: "missing_tools",
      failure_title: "Missing tools",
      risk_weight: 0.25,
      description: "No executable tools were declared.",
      why_it_matters: "The agent may be unable to complete tasks that require tool execution.",
      suggested_fix: "Add at least one executable tool.",
      patch: {
        tools: ["search_docs"]
      },
      affected_area: "tools"
    });
  }

  function checkFallbackRoute(config) {
    var ok = isPlainObject(config.routing) && hasText(config.routing.fallback);
    return ruleResult({
      rule_id: "fallback_route_configured",
      title: "Fallback route configured",
      status: ok ? "pass" : "fail",
      severity: "high",
      detail: ok ? "routing.fallback is configured" : "routing.fallback is missing",
      failure_id: "missing_fallback_route",
      failure_title: "Missing fallback route",
      risk_weight: 0.20,
      description: "No fallback route is configured for uncertain or failed execution.",
      why_it_matters: "Without a fallback route, the agent may continue autonomously when it should stop, ask for help, or escalate.",
      suggested_fix: "Add a fallback route such as human_review.",
      patch: {
        routing: {
          fallback: "human_review"
        }
      },
      affected_area: "routing"
    });
  }

  function checkMemoryRetention(config) {
    var memory = isPlainObject(config.memory) ? config.memory : {};
    var enabled = memory.enabled === true;
    var retention = Number(memory.retention_days);
    var unsafe = enabled && Number.isFinite(retention) && retention > 90;
    return ruleResult({
      rule_id: "memory_retention_safe",
      title: "Memory retention safe",
      status: unsafe ? "fail" : "pass",
      severity: "medium",
      detail: unsafe ? "memory.retention_days is greater than 90" : "memory is disabled, missing, or within the demo threshold",
      failure_id: "unsafe_memory_retention",
      failure_title: "Unsafe memory retention",
      risk_weight: 0.15,
      description: "Memory retention is enabled for longer than the demo safety threshold.",
      why_it_matters: "Long retention can increase privacy, compliance, and stale-context risk.",
      suggested_fix: "Reduce memory retention to a safer default.",
      patch: {
        memory: {
          retention_days: 30
        }
      },
      affected_area: "memory"
    });
  }

  function checkTokenBudget(config) {
    var budget = isPlainObject(config.budget) ? config.budget : {};
    if (!Object.prototype.hasOwnProperty.call(budget, "max_tokens")) {
      return ruleResult({
        rule_id: "token_budget_guardrail",
        title: "Token budget guardrail",
        status: "warn",
        severity: "low",
        detail: "budget.max_tokens is missing",
        failure_id: "missing_token_budget",
        failure_title: "Missing token budget",
        risk_weight: 0.05,
        description: "No token budget guardrail was declared.",
        why_it_matters: "A missing budget makes cost and runaway-execution risk harder to bound before deployment.",
        suggested_fix: "Add token budget guardrails.",
        patch: {
          budget: {
            max_tokens: 50000
          }
        },
        affected_area: "budget"
      });
    }

    var maxTokens = Number(budget.max_tokens);
    var excessive = Number.isFinite(maxTokens) && maxTokens > 100000;
    return ruleResult({
      rule_id: "token_budget_guardrail",
      title: "Token budget guardrail",
      status: excessive ? "fail" : "pass",
      severity: excessive ? "medium" : "low",
      detail: excessive ? "budget.max_tokens is greater than 100000" : "budget.max_tokens is within the demo threshold",
      failure_id: "excessive_token_budget",
      failure_title: "Excessive token budget",
      risk_weight: 0.15,
      description: "The configured token budget is above the demo threshold.",
      why_it_matters: "Very high token limits can hide loops, increase spend, and make diagnosis slower.",
      suggested_fix: "Add or reduce token budget guardrails.",
      patch: {
        budget: {
          max_tokens: 50000
        }
      },
      affected_area: "budget"
    });
  }

  function checkOutputSchema(config) {
    var ok = Boolean(config.output_schema) || (isPlainObject(config.schema) && Boolean(config.schema.output));
    return ruleResult({
      rule_id: "output_schema_present",
      title: "Output schema present",
      status: ok ? "pass" : "fail",
      severity: "medium",
      detail: ok ? "output_schema or schema.output is present" : "output schema is missing",
      failure_id: "missing_output_schema",
      failure_title: "Missing output schema",
      risk_weight: 0.10,
      description: "No output schema was declared.",
      why_it_matters: "Downstream consumers and regression checks need a schema to validate response shape reliably.",
      suggested_fix: "Define an output schema so downstream consumers can validate responses.",
      patch: {
        output_schema: {
          type: "object",
          required: ["answer"],
          properties: {
            answer: {
              type: "string"
            }
          }
        }
      },
      affected_area: "output_schema"
    });
  }

  function checkEvaluationPolicy(config) {
    var ok = Boolean(config.evaluation) || Boolean(config.eval_policy);
    return ruleResult({
      rule_id: "evaluation_policy_present",
      title: "Evaluation policy present",
      status: ok ? "pass" : "fail",
      severity: "low",
      detail: ok ? "evaluation or eval_policy is present" : "evaluation policy is missing",
      failure_id: "missing_evaluation_policy",
      failure_title: "Missing evaluation policy",
      risk_weight: 0.05,
      description: "No evaluation policy was declared.",
      why_it_matters: "Regression checks need a policy that says what acceptable behavior means.",
      suggested_fix: "Add an evaluation policy for regression checks.",
      patch: {
        evaluation: {
          enabled: true,
          min_pass_rate: 0.95
        }
      },
      affected_area: "evaluation"
    });
  }

  function checkHumanReviewGate(config, accumulatedRisk) {
    var hasReviewGate = isPlainObject(config.review) && config.review.human_required === true;
    var hasFallbackGate = isPlainObject(config.routing) && config.routing.fallback === "human_review";
    var shouldWarn = !hasReviewGate && !hasFallbackGate && accumulatedRisk > 0.5;
    return ruleResult({
      rule_id: "human_review_for_high_risk",
      title: "Human review for high risk",
      status: shouldWarn ? "warn" : "pass",
      severity: "medium",
      detail: shouldWarn ? "high-risk configuration has no human review gate" : "human review gate is present or risk is below high",
      failure_id: "missing_human_review_gate",
      failure_title: "Missing human review gate",
      risk_weight: 0.10,
      description: "The current accumulated risk is high, but no human review gate is configured.",
      why_it_matters: "High-risk deployments should route uncertain behavior to a human before release or escalation.",
      suggested_fix: "Add a human review gate for high-risk deployments.",
      patch: {
        review: {
          human_required: true
        }
      },
      affected_area: "review"
    });
  }

  function ruleResult(fields) {
    return fields;
  }

  function computeRiskScore(failures) {
    var total = failures.reduce(function (sum, failure) {
      return sum + Number(failure.risk_weight || 0);
    }, 0);
    return Math.min(1, Math.round(total * 100) / 100);
  }

  function deriveSeverity(riskScore) {
    if (riskScore <= 0.20) {
      return "low";
    }
    if (riskScore <= 0.50) {
      return "medium";
    }
    if (riskScore <= 0.80) {
      return "high";
    }
    return "critical";
  }

  function deriveStatus(riskScore) {
    if (riskScore === 0) {
      return "pass";
    }
    if (riskScore <= 0.5) {
      return "warning";
    }
    return "fail";
  }

  function buildMinimalPatch(failures) {
    return failures.reduce(function (patch, failure) {
      return mergePatch(patch, failure.patch || {});
    }, {});
  }

  function mergePatch(base, nextPatch) {
    var result = clone(base);
    Object.keys(nextPatch).forEach(function (key) {
      var value = nextPatch[key];
      if (isPlainObject(value) && isPlainObject(result[key])) {
        result[key] = mergePatch(result[key], value);
      } else {
        result[key] = clone(value);
      }
    });
    return result;
  }

  function estimateEffort(failures) {
    var count = failures.length;
    var estimate;
    if (count === 0) {
      estimate = {
        fix_time_minutes: "0",
        review_cost: "low",
        regression_risk: "low"
      };
    } else if (count <= 2) {
      estimate = {
        fix_time_minutes: "3-6",
        review_cost: "low",
        regression_risk: "low"
      };
    } else if (count <= 4) {
      estimate = {
        fix_time_minutes: "8-12",
        review_cost: "medium",
        regression_risk: "medium"
      };
    } else {
      estimate = {
        fix_time_minutes: "15-30",
        review_cost: "high",
        regression_risk: "high"
      };
    }

    if (failures.some(function (failure) {
      return ["routing", "memory", "output_schema"].indexOf(failure.affected_area) !== -1;
    })) {
      estimate.review_cost = increaseLevel(estimate.review_cost);
    }

    return estimate;
  }

  function increaseLevel(level) {
    if (level === "low") {
      return "medium";
    }
    if (level === "medium") {
      return "high";
    }
    return level;
  }

  function buildRegressionTrace(coverage) {
    var labels = {
      agent_identity_present: "Checked agent identity.",
      tools_available: "Checked tool availability.",
      fallback_route_configured: "Checked routing fallback.",
      memory_retention_safe: "Checked memory retention policy.",
      token_budget_guardrail: "Checked token budget guardrail.",
      output_schema_present: "Checked output schema.",
      evaluation_policy_present: "Checked evaluation policy.",
      human_review_for_high_risk: "Checked human review gate."
    };
    var trace = ["Parsed JSON configuration successfully."];
    coverage.forEach(function (item) {
      trace.push(labels[item.rule_id] || "Checked " + item.title + ".");
    });
    return trace;
  }

  function toFailureType(failure) {
    return {
      id: failure.id,
      title: failure.title,
      severity: failure.severity,
      description: failure.description,
      why_it_matters: failure.why_it_matters,
      suggested_fix: failure.suggested_fix
    };
  }

  function renderReport(elements, report) {
    elements.reportOutput.replaceChildren();
    elements.reportOutput.appendChild(renderSummaryCards(report));
    elements.reportOutput.appendChild(renderFailures(report));
    elements.reportOutput.appendChild(renderSuggestedFixes(report));
    elements.reportOutput.appendChild(renderPatch(report));
    elements.reportOutput.appendChild(renderEffort(report));
    elements.reportOutput.appendChild(renderTrace(report));
    elements.reportOutput.appendChild(renderCoverage(report));
    elements.reportOutput.appendChild(renderJsonReport(report));
  }

  function renderSummaryCards(report) {
    var section = createSection("Summary");
    var grid = el("div", "c2a-demo__summary-grid");
    grid.appendChild(summaryCard("Status", report.status, report.status));
    grid.appendChild(summaryCard("Severity", report.severity, report.severity));
    grid.appendChild(summaryCard("Risk score", report.risk_score.toFixed(2), report.severity));
    grid.appendChild(summaryCard("Failed rules", String(report.summary.failed_rules), report.summary.failed_rules ? "warning" : "pass"));
    section.appendChild(grid);
    return section;
  }

  function renderFailures(report) {
    var section = createSection("Detected failures");
    if (!report.failure_types.length) {
      section.appendChild(el("p", "c2a-demo__muted", "No failures detected by the demo rule set."));
      return section;
    }
    report.failure_types.forEach(function (failure) {
      var card = el("article", "c2a-demo__failure-card");
      var header = el("div", "c2a-demo__card-header");
      header.appendChild(el("h4", "", failure.title));
      header.appendChild(statusBadge(failure.severity));
      card.appendChild(header);
      card.appendChild(labeledText("Failure id", failure.id));
      card.appendChild(labeledText("Description", failure.description));
      card.appendChild(labeledText("Why it matters", failure.why_it_matters));
      section.appendChild(card);
    });
    return section;
  }

  function renderSuggestedFixes(report) {
    var section = createSection("Suggested fixes");
    if (!report.suggested_fixes.length) {
      section.appendChild(el("p", "c2a-demo__muted", "No remediation guidance needed for this demo run."));
      return section;
    }
    var list = el("ul", "c2a-demo__fix-list");
    report.suggested_fixes.forEach(function (fix) {
      var item = document.createElement("li");
      item.appendChild(el("strong", "", fix.title + ": "));
      item.appendChild(document.createTextNode(fix.suggested_fix));
      list.appendChild(item);
    });
    section.appendChild(list);
    return section;
  }

  function renderPatch(report) {
    var section = createSection("Minimal patch preview");
    section.appendChild(jsonBlock(report.minimal_patch));
    return section;
  }

  function renderEffort(report) {
    var section = createSection("Estimated fix effort");
    var grid = el("div", "c2a-demo__summary-grid c2a-demo__summary-grid--three");
    grid.appendChild(summaryCard("Fix time", report.estimated_effort.fix_time_minutes + " min", "info"));
    grid.appendChild(summaryCard("Review cost", report.estimated_effort.review_cost, report.estimated_effort.review_cost));
    grid.appendChild(summaryCard("Regression risk", report.estimated_effort.regression_risk, report.estimated_effort.regression_risk));
    section.appendChild(grid);
    return section;
  }

  function renderTrace(report) {
    var section = createSection("Regression trace");
    var list = el("ol", "c2a-demo__trace-list");
    report.regression_trace.forEach(function (line) {
      list.appendChild(el("li", "", line));
    });
    section.appendChild(list);
    return section;
  }

  function renderCoverage(report) {
    var section = createSection("Rule coverage matrix");
    var wrap = el("div", "c2a-demo__table-wrap");
    var table = el("table", "c2a-demo__table");
    var thead = document.createElement("thead");
    var header = document.createElement("tr");
    ["Rule", "Status", "Severity", "Detail"].forEach(function (text) {
      header.appendChild(el("th", "", text));
    });
    thead.appendChild(header);
    table.appendChild(thead);

    var tbody = document.createElement("tbody");
    report.rule_coverage.forEach(function (item) {
      var row = document.createElement("tr");
      row.appendChild(el("td", "", item.title));
      var statusCell = document.createElement("td");
      statusCell.appendChild(statusBadge(item.status));
      row.appendChild(statusCell);
      var severityCell = document.createElement("td");
      severityCell.appendChild(statusBadge(item.severity));
      row.appendChild(severityCell);
      row.appendChild(el("td", "", item.detail));
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    section.appendChild(wrap);
    return section;
  }

  function renderJsonReport(report) {
    var section = createSection("Machine-readable JSON report");
    section.appendChild(jsonBlock(report));
    return section;
  }

  function renderError(elements, message) {
    currentReport = null;
    setReportActionsEnabled(elements, false);
    setInputStatus(elements, message, "error");
    setReportStatus(elements, "Diagnosis stopped because the input JSON is invalid.", "error");
    elements.reportOutput.replaceChildren();
    var errorBox = el("div", "c2a-demo__error-box");
    errorBox.appendChild(el("strong", "", "Invalid JSON"));
    errorBox.appendChild(el("span", "", message));
    elements.reportOutput.appendChild(errorBox);
  }

  function clearReport(elements, message) {
    currentReport = null;
    setReportActionsEnabled(elements, false);
    setReportStatus(elements, message || "No current report.", "info");
    elements.reportOutput.replaceChildren();
    var empty = el("div", "c2a-demo__empty-state");
    empty.appendChild(el("strong", "", "No current report."));
    empty.appendChild(el("span", "", "Run diagnosis to generate fresh results."));
    elements.reportOutput.appendChild(empty);
  }

  function formatJsonInput(elements) {
    var parsed = parseConfig(elements.input.value);
    if (!parsed.ok) {
      renderError(elements, parsed.error);
      return;
    }
    elements.input.value = stringify(parsed.value);
    saveInputToLocalStorage(elements.input.value);
    updateInputStatus(elements);
    setReportStatus(elements, "JSON formatted. Run diagnosis to refresh the report.", "info");
  }

  function clearInput(elements) {
    elements.input.value = "";
    saveInputToLocalStorage("");
    setInputStatus(elements, "Configuration JSON is required.", "error");
    clearReport(elements, "Input cleared.");
  }

  function updateInputStatus(elements) {
    var parsed = parseConfig(elements.input.value);
    if (parsed.ok) {
      setInputStatus(elements, "Valid JSON.", "success");
    } else {
      setInputStatus(elements, parsed.error, "error");
    }
  }

  function copyToClipboard(text, elements, successMessage) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () {
        setReportStatus(elements, successMessage, "success");
      }).catch(function () {
        fallbackCopy(text, elements, successMessage);
      });
      return;
    }
    fallbackCopy(text, elements, successMessage);
  }

  function fallbackCopy(text, elements, successMessage) {
    var buffer = document.createElement("textarea");
    buffer.value = text;
    buffer.setAttribute("readonly", "");
    buffer.className = "c2a-demo__copy-buffer";
    document.body.appendChild(buffer);
    buffer.select();
    var copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (error) {
      copied = false;
    }
    document.body.removeChild(buffer);
    setReportStatus(
      elements,
      copied ? successMessage : "Clipboard is unavailable. Select the visible report block and copy manually.",
      copied ? "success" : "error"
    );
  }

  function downloadTextFile(filename, text, mimeType) {
    var blob = new Blob([text], { type: mimeType + ";charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 0);
  }

  function buildMarkdownReport(report) {
    var lines = [
      "# Contract2Agent Demo Report",
      "",
      "- Status: " + report.status,
      "- Severity: " + report.severity,
      "- Risk score: " + report.risk_score.toFixed(2),
      "",
      "## Detected Failures",
      ""
    ];

    if (!report.failure_types.length) {
      lines.push("No failures detected by the demo rule set.", "");
    } else {
      report.failure_types.forEach(function (failure) {
        lines.push("- `" + failure.id + "` (" + failure.severity + "): " + failure.title);
        lines.push("  " + failure.description);
      });
      lines.push("");
    }

    lines.push("## Suggested Fixes", "");
    if (!report.suggested_fixes.length) {
      lines.push("No fixes needed.", "");
    } else {
      report.suggested_fixes.forEach(function (fix) {
        lines.push("- " + fix.title + ": " + fix.suggested_fix);
      });
      lines.push("");
    }

    lines.push("## Minimal Patch", "", "```json", JSON.stringify(report.minimal_patch, null, 2), "```", "");
    lines.push("## Estimated Effort", "");
    lines.push("- Fix time: " + report.estimated_effort.fix_time_minutes + " minutes");
    lines.push("- Review cost: " + report.estimated_effort.review_cost);
    lines.push("- Regression risk: " + report.estimated_effort.regression_risk);
    lines.push("");

    lines.push("## Regression Trace", "");
    report.regression_trace.forEach(function (step, index) {
      lines.push(String(index + 1) + ". " + step);
    });
    lines.push("");

    lines.push("## Rule Coverage Matrix", "");
    lines.push("| Rule | Status | Severity | Detail |");
    lines.push("|---|---|---|---|");
    report.rule_coverage.forEach(function (item) {
      lines.push("| " + escapeMarkdownTable(item.title) + " | " + item.status + " | " + item.severity + " | " + escapeMarkdownTable(item.detail) + " |");
    });

    return lines.join("\n") + "\n";
  }

  function setInputStatus(elements, message, level) {
    elements.inputStatus.textContent = message;
    elements.inputStatus.className = "c2a-demo__status c2a-demo__status--" + level;
  }

  function setReportStatus(elements, message, level) {
    elements.reportStatus.textContent = message;
    elements.reportStatus.className = "c2a-demo__status c2a-demo__status--" + level;
  }

  function setReportActionsEnabled(elements, enabled) {
    [elements.copyJson, elements.copyPatch, elements.downloadJson, elements.downloadMarkdown].forEach(function (button) {
      button.disabled = !enabled;
    });
  }

  function saveInputToLocalStorage(text) {
    try {
      if (text) {
        window.localStorage.setItem(STORAGE_KEY, text);
      } else {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    } catch (error) {
      return false;
    }
    return true;
  }

  function loadInputFromLocalStorage() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return "";
    }
  }

  function createSection(title) {
    var section = el("section", "c2a-demo__section");
    section.appendChild(el("h3", "", title));
    return section;
  }

  function summaryCard(label, value, tone) {
    var card = el("div", "c2a-demo__summary-card c2a-demo__summary-card--" + safeClass(tone));
    card.appendChild(el("span", "c2a-demo__summary-label", label));
    card.appendChild(el("strong", "c2a-demo__summary-value", value));
    return card;
  }

  function labeledText(label, text) {
    var wrapper = el("div", "c2a-demo__labeled");
    wrapper.appendChild(el("span", "c2a-demo__label", label));
    wrapper.appendChild(el("p", "", text));
    return wrapper;
  }

  function statusBadge(value) {
    return el("span", "c2a-demo__badge c2a-demo__badge--" + safeClass(value), value);
  }

  function jsonBlock(value) {
    var block = el("pre", "c2a-demo__code-block");
    block.tabIndex = 0;
    block.textContent = stringify(value);
    return block;
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

  function stringify(value) {
    return JSON.stringify(value, null, 2);
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function hasText(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function safeClass(value) {
    return String(value || "none").toLowerCase().replace(/[^a-z0-9_-]/g, "-");
  }

  function escapeMarkdownTable(value) {
    return String(value || "").replace(/\|/g, "\\|").replace(/\n/g, " ");
  }
}());
