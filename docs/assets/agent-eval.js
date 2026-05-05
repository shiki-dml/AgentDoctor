(function () {
  "use strict";

  const TYPE_DEFS = [
    {
      type_id: "coding_agent",
      label: "Coding Agent",
      capability_signals: ["code", "repository", "repo", "patch", "test", "build", "diff"],
      tool_signals: ["shell", "terminal", "pytest", "git", "file_write", "code_editor", "apply_patch", "compiler", "test_runner"],
      task_signals: ["fix failing test", "repair bug", "edit code", "run tests", "build", "minimal patch", "patch"],
      eval_categories: ["coding_change_safety", "tool_and_permission_safety", "trace_and_state_observability"],
      evidence_requirements: ["patch artifact", "test/build output", "command trace"]
    },
    {
      type_id: "file_reading_agent",
      label: "File Reading Agent",
      capability_signals: ["file", "document", "read", "citation", "source", "pdf"],
      tool_signals: ["file_read", "reader", "pdf_reader", "document_reader", "citation", "search_local"],
      task_signals: ["cite source", "answer from files", "summarize document", "missing file", "quote evidence"],
      eval_categories: ["document_grounding", "evidence_and_citation_quality", "tool_and_permission_safety"],
      evidence_requirements: ["provided file corpus", "answer-to-source trace", "missing-file behavior test"]
    },
    {
      type_id: "browser_navigation_agent",
      label: "Browser Navigation Agent",
      capability_signals: ["browser", "web navigation", "website", "page", "form"],
      tool_signals: ["browser", "navigate", "click", "dom", "screenshot", "form", "submit"],
      task_signals: ["navigate", "fill form", "verify page", "gather web", "submit form"],
      eval_categories: ["browser_task_flow", "side_effect_and_approval_safety", "trace_and_state_observability"],
      evidence_requirements: ["controlled browser trace", "page-state validation", "approval record for submit actions"]
    },
    {
      type_id: "contract_review_agent",
      label: "Contract Review Agent",
      capability_signals: ["contract", "clause", "obligation", "legal", "rule", "policy"],
      tool_signals: ["contract_parser", "clause_extractor", "document_reader", "pdf_reader", "citation"],
      task_signals: ["review contract", "identify obligation", "evidence gap", "clause", "fact pattern"],
      eval_categories: ["document_grounding", "evidence_and_citation_quality", "trace_and_state_observability"],
      evidence_requirements: ["source document", "clause-to-output trace", "uncertainty handling checks"]
    },
    {
      type_id: "research_agent",
      label: "Research Agent",
      capability_signals: ["research", "source", "citation", "evidence", "freshness", "paper"],
      tool_signals: ["web_search", "search", "browser", "reader", "citation", "scholar"],
      task_signals: ["find sources", "synthesize evidence", "conflicting evidence", "cite", "freshness"],
      eval_categories: ["research_source_quality", "evidence_and_citation_quality", "trace_and_state_observability"],
      evidence_requirements: ["source list", "citation-to-claim trace", "conflicting-evidence task"]
    },
    {
      type_id: "workflow_automation_agent",
      label: "Workflow Automation Agent",
      capability_signals: ["workflow", "automation", "handoff", "routing", "state", "orchestration"],
      tool_signals: ["scheduler", "queue", "router", "email", "calendar", "workflow", "handoff"],
      task_signals: ["multi-step", "handoff", "route", "state tracking", "loop control", "approval workflow"],
      eval_categories: ["workflow_state_control", "side_effect_and_approval_safety", "trace_and_state_observability"],
      evidence_requirements: ["multi-step trace", "state transition record", "loop and handoff boundary tests"]
    },
    {
      type_id: "financial_transaction_agent_simulated",
      label: "Financial Transaction Agent (Simulated)",
      capability_signals: ["payment", "transaction", "trade", "order", "checkout", "transfer"],
      tool_signals: ["payment", "transfer", "trade", "order", "checkout", "bank", "card", "transaction"],
      task_signals: ["authorize payment", "confirm transfer", "place order", "simulate trade", "audit trail", "refuse unsafe"],
      eval_categories: ["simulated_transaction_safety", "side_effect_and_approval_safety", "trace_and_state_observability"],
      evidence_requirements: ["simulation sandbox", "approval trace", "refusal tests for unsafe transaction requests"],
      simulation_only: true
    },
    {
      type_id: "general_tool_use_agent",
      label: "General Tool-Use Agent",
      capability_signals: ["tool", "api", "action", "assistant"],
      tool_signals: ["tool", "api", "connector", "integration", "function"],
      task_signals: ["use tool", "call api", "complete task", "take action"],
      eval_categories: ["tool_and_permission_safety", "trace_and_state_observability"],
      evidence_requirements: ["tool inventory", "sample task trace", "permission boundary description"]
    }
  ];

  const FALLBACK_CATEGORIES = [
    { category_id: "profile_completion", label: "Profile Completion", applicable_agent_types: ["unknown_agent"], required_evidence: ["tools", "sample tasks", "permission boundaries"], limitations: ["No performance score is available for sparse profiles."] },
    { category_id: "trace_and_state_observability", label: "Trace And State Observability", applicable_agent_types: ["coding_agent", "browser_navigation_agent", "contract_review_agent", "research_agent", "workflow_automation_agent", "financial_transaction_agent_simulated", "general_tool_use_agent"], required_evidence: ["trace summary", "artifacts", "verdict"], limitations: ["Trace availability does not by itself prove correctness."] }
  ];

  const FALLBACK_SOURCES = [
    {
      source_id: "openai_agent_evals_methodology",
      source_type: "curated_research_reference",
      title: "OpenAI agent evaluation methodology",
      url: "https://developers.openai.com/api/docs/guides/agent-evals",
      reliability: 0.2,
      applies_to: ["evaluation_methodology", "workflow_automation_agent", "research_agent"],
      limitations: ["Methodology reference only.", "No API call is made by this page."]
    },
    {
      source_id: "swe_bench_reference",
      source_type: "benchmark_reference",
      title: "SWE-bench",
      url: "https://www.swebench.com/SWE-bench/guides/evaluation/",
      reliability: 0.2,
      applies_to: ["coding_agent"],
      limitations: ["No score is assigned without a linked experiment summary."]
    },
    {
      source_id: "webarena_reference",
      source_type: "benchmark_reference",
      title: "WebArena",
      url: "https://github.com/web-arena-x/webarena",
      reliability: 0.2,
      applies_to: ["browser_navigation_agent"],
      limitations: ["No score is assigned without a linked experiment summary."]
    }
  ];

  const FALLBACK_SAMPLE_PROFILES = [
    {
      profile_id: "vague_unknown_agent",
      label: "Vague unknown agent",
      description: "A helpful assistant that can do many tasks.",
      declared_capabilities: "help users, answer questions",
      tools: "",
      tool_permissions: "",
      sample_tasks: "",
      policy_constraints: "",
      experiment_summary: "",
      can_read_files: false,
      can_write_files: false,
      can_run_code: false,
      can_use_browser: false,
      can_use_network: false,
      can_execute_transactions: false,
      can_modify_external_state: false,
      requires_human_approval: false,
      autonomy_level: "unknown"
    },
    {
      profile_id: "coding_file_reading_hybrid",
      label: "Coding / file-reading hybrid",
      description: "Reads repository files, edits local code, runs tests, and cites file evidence in patch reports.",
      declared_capabilities: "read files, edit code, run tests, summarize diffs, cite sources",
      tools: "file_reader, search_local, code_editor, shell, test_runner",
      tool_permissions: "read_workspace, write_workspace, run_tests, cite_file_paths",
      sample_tasks: "Fix failing tests with a minimal patch. Answer implementation questions from repository files with citations.",
      policy_constraints: "Stay inside the workspace. Do not run destructive commands. Report test output and changed files.",
      experiment_summary: "",
      can_read_files: true,
      can_write_files: true,
      can_run_code: true,
      can_use_browser: false,
      can_use_network: false,
      can_execute_transactions: false,
      can_modify_external_state: false,
      requires_human_approval: true,
      autonomy_level: "medium"
    },
    {
      profile_id: "browser_navigation_agent",
      label: "Browser-navigation agent",
      description: "Uses a browser to navigate websites, inspect page state, fill forms, and gather web information under approval controls.",
      declared_capabilities: "browser navigation, web page inspection, form filling, page-state verification",
      tools: "browser, navigate, click, dom_inspector, screenshot, form_filler",
      tool_permissions: "read_web_pages, fill_forms, submit_only_after_approval, capture_screenshots",
      sample_tasks: "Navigate to a site, gather information, fill a form, verify page state, and do not submit without approval.",
      policy_constraints: "No unapproved submit actions. Explicit approval is required before changing external state.",
      experiment_summary: "",
      can_read_files: false,
      can_write_files: false,
      can_run_code: false,
      can_use_browser: true,
      can_use_network: true,
      can_execute_transactions: false,
      can_modify_external_state: true,
      requires_human_approval: true,
      autonomy_level: "medium"
    },
    {
      profile_id: "simulated_financial_transaction_agent",
      label: "Simulated financial transaction agent",
      description: "Simulates payment, order, and transfer workflows with explicit confirmation and audit logging.",
      declared_capabilities: "simulate payment, authorize transaction, confirm transfer, produce audit trail, refuse unsafe requests",
      tools: "simulated_payment_gateway, simulated_order_tool, confirmation_prompt, audit_log",
      tool_permissions: "simulation_only, requires_approval, no_real_funds, audit_log_required",
      sample_tasks: "Authorize a simulated payment only after explicit confirmation. Refuse unapproved transfer requests. Produce an audit trail.",
      policy_constraints: "Simulation only. No real funds, cards, bank accounts, trades, or orders. Explicit approval required.",
      experiment_summary: "",
      can_read_files: false,
      can_write_files: false,
      can_run_code: false,
      can_use_browser: false,
      can_use_network: false,
      can_execute_transactions: true,
      can_modify_external_state: false,
      requires_human_approval: true,
      autonomy_level: "low"
    },
    {
      profile_id: "contract_review_agent",
      label: "Contract-review agent",
      description: "Reads contract documents, identifies clauses and obligations, separates facts from clauses, and reports evidence gaps with citations.",
      declared_capabilities: "review contract, identify obligations, extract clauses, cite sources, identify evidence gaps",
      tools: "document_reader, contract_parser, clause_extractor, citation",
      tool_permissions: "read_documents, cite_clauses, no_legal_advice_final_decision",
      sample_tasks: "Review a contract, identify obligations, cite supporting clauses, flag missing evidence, and distinguish facts from contract terms.",
      policy_constraints: "Do not make unsupported legal conclusions. Cite source clauses and mark missing facts.",
      experiment_summary: "",
      can_read_files: true,
      can_write_files: false,
      can_run_code: false,
      can_use_browser: false,
      can_use_network: false,
      can_execute_transactions: false,
      can_modify_external_state: false,
      requires_human_approval: true,
      autonomy_level: "low"
    }
  ];

  const state = {
    categories: FALLBACK_CATEGORIES,
    sources: FALLBACK_SOURCES,
    sampleProfiles: FALLBACK_SAMPLE_PROFILES
  };

  document.addEventListener("DOMContentLoaded", () => {
    populateSampleSelector(state.sampleProfiles);
    loadStaticData();
    const form = document.getElementById("agent-eval-form");
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runEvaluation();
    });
    document.getElementById("load-sample-profile").addEventListener("click", loadSelectedSampleProfile);
    document.getElementById("sample-profile").addEventListener("change", loadSelectedSampleProfile);
    runEvaluation();
  });

  async function loadStaticData() {
    const [categoryData, sourceData, sampleData] = await Promise.all([
      loadJson("../data/agent_eval/eval_categories.json"),
      loadJson("../data/agent_eval/source_references.json"),
      loadJson("../data/agent_eval/sample_profiles.json")
    ]);
    if (categoryData && Array.isArray(categoryData.eval_categories)) {
      state.categories = categoryData.eval_categories;
    }
    if (sourceData && Array.isArray(sourceData.sources)) {
      state.sources = sourceData.sources;
    }
    if (sampleData && Array.isArray(sampleData.profiles) && sampleData.profiles.length) {
      state.sampleProfiles = sampleData.profiles;
      populateSampleSelector(state.sampleProfiles);
    }
    runEvaluation();
  }

  async function loadJson(path) {
    if (typeof fetch !== "function") {
      return null;
    }
    try {
      const response = await fetch(path);
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch (_error) {
      return null;
    }
  }

  function runEvaluation() {
    const profile = collectProfile();
    const experiment = parseExperimentSummary(profile);
    const report = analyzeProfile(profile, experiment);
    renderReport(report);
  }

  function populateSampleSelector(profiles) {
    const select = document.getElementById("sample-profile");
    if (!select || !profiles.length) {
      return;
    }
    const currentValue = select.value || "coding_file_reading_hybrid";
    select.innerHTML = profiles.map((profile) => {
      const selected = profile.profile_id === currentValue ? " selected" : "";
      return `<option value="${escapeHtml(profile.profile_id)}"${selected}>${escapeHtml(profile.label || profile.profile_id)}</option>`;
    }).join("");
    if (!profiles.some((profile) => profile.profile_id === select.value)) {
      select.value = profiles[0].profile_id;
    }
  }

  function loadSelectedSampleProfile() {
    const selectedId = valueOf("sample-profile");
    const profile = state.sampleProfiles.find((item) => item.profile_id === selectedId) || state.sampleProfiles[0];
    if (!profile) {
      return;
    }
    applySampleProfile(profile);
    runEvaluation();
  }

  function applySampleProfile(profile) {
    setValue("agent-name", profile.name || profile.label || "Sample agent");
    setValue("agent-description", textField(profile.description));
    setValue("declared-capabilities", textField(profile.declared_capabilities));
    setValue("tool-names", textField(profile.tools));
    setValue("tool-permissions", textField(profile.tool_permissions));
    setValue("sample-tasks", textField(profile.sample_tasks));
    setValue("policy-constraints", textField(profile.policy_constraints));
    setValue("experiment-summary", textField(profile.experiment_summary));
    setValue("autonomy-level", profile.autonomy_level || "unknown");
    setChecked("can-read-files", profile.can_read_files);
    setChecked("can-write-files", profile.can_write_files);
    setChecked("can-run-code", profile.can_run_code);
    setChecked("can-use-browser", profile.can_use_browser);
    setChecked("can-use-network", profile.can_use_network);
    setChecked("can-execute-transactions", profile.can_execute_transactions);
    setChecked("can-modify-external-state", profile.can_modify_external_state);
    setChecked("requires-human-approval", profile.requires_human_approval);
  }

  function collectProfile() {
    const tools = listFromText(valueOf("tool-names"));
    return {
      agent_id: "demo-agent",
      name: valueOf("agent-name").trim() || "Unnamed agent",
      description: valueOf("agent-description"),
      declared_capabilities: listFromText(valueOf("declared-capabilities")),
      tools,
      tool_permissions: listFromText(valueOf("tool-permissions")),
      can_read_files: checked("can-read-files"),
      can_write_files: checked("can-write-files"),
      can_run_code: checked("can-run-code"),
      can_use_browser: checked("can-use-browser"),
      can_use_network: checked("can-use-network"),
      can_execute_transactions: checked("can-execute-transactions"),
      can_modify_external_state: checked("can-modify-external-state"),
      requires_human_approval: checked("requires-human-approval"),
      autonomy_level: valueOf("autonomy-level"),
      sample_tasks: splitSentences(valueOf("sample-tasks")),
      policy_constraints: splitSentences(valueOf("policy-constraints"))
    };
  }

  function parseExperimentSummary(profile) {
    const raw = valueOf("experiment-summary").trim();
    if (!raw) {
      return null;
    }
    try {
      const parsed = JSON.parse(raw);
      return {
        result_id: parsed.result_id || parsed.run_id || "pasted-experiment",
        agent_id: profile.agent_id,
        agent_type: parsed.agent_type || "",
        eval_category: parsed.eval_category || parsed.eval_pack_id || "trace_and_state_observability",
        verdict: parsed.verdict || "user_pasted",
        evidence_source: parsed.evidence_source || "observed_experiment",
        trace_available: Boolean(parsed.trace_available || parsed.trace_summary),
        limitations: ["Pasted summary is user-provided and not independently verified."]
      };
    } catch (_error) {
      return {
        result_id: "pasted-summary",
        agent_id: profile.agent_id,
        agent_type: "",
        eval_category: "trace_and_state_observability",
        verdict: "user_pasted_summary",
        evidence_source: raw.toLowerCase().includes("trace") ? "imported_trace" : "observed_experiment",
        trace_available: /trace|log|tool|test|verdict/i.test(raw),
        limitations: ["Pasted summary is user-provided and not independently verified."],
        notes: raw.slice(0, 240)
      };
    }
  }

  function analyzeProfile(profile, experiment) {
    const classification = classifyProfile(profile);
    const categories = selectCategories(classification);
    const sources = resolveSources(classification, experiment);
    const missing = missingEvidence(profile, classification, categories, experiment, sources);
    const scores = scoreProfile(profile, classification, experiment, missing, sources);
    const prediction = predictOutcome(classification, scores, missing, experiment);
    return {
      agent_profile: profile,
      classification,
      inferred_capabilities: inferredCapabilities(classification),
      applicable_eval_categories: categories,
      preliminary_scores: scores,
      outcome_prediction: prediction,
      evidence_summary: sources,
      missing_evidence: missing,
      limitations: [
        "This static page performs preliminary classification only.",
        "Benchmark references are contextual and are not direct scores.",
        "Financial transaction workflows are simulation-only.",
        "Run real eval categories and import traces before relying on predictions."
      ]
    };
  }

  function classifyProfile(profile) {
    const declaredText = normalize([profile.description].concat(profile.declared_capabilities, profile.policy_constraints));
    const toolText = normalize(profile.tools.concat(profile.tool_permissions));
    const taskText = normalize(profile.sample_tasks);
    const scores = TYPE_DEFS.map((def) => {
      const signals = [];
      let confidence = 0;
      matchSignals(def.capability_signals, declaredText).forEach((value) => {
        confidence += 0.08;
        signals.push(signal(def.type_id, "declared", "description/declared_capabilities", value, "low", 0.08));
      });
      matchSignals(def.tool_signals, toolText).forEach((value) => {
        confidence += 0.17;
        signals.push(signal(def.type_id, "tool", "tools/tool_permissions", value, "medium", 0.17));
      });
      matchSignals(def.task_signals, taskText).forEach((value) => {
        confidence += 0.14;
        signals.push(signal(def.type_id, "task", "sample_tasks", value, "medium", 0.14));
      });
      profileFlagSignals(profile, def.type_id).forEach((item) => {
        confidence += item.confidence;
        signals.push(signal(def.type_id, "profile_flag", "profile_flags", item.value, "medium", item.confidence));
      });
      return {
        type_id: def.type_id,
        label: def.label,
        confidence: Math.min(0.96, confidence),
        signals
      };
    }).sort((a, b) => b.confidence - a.confidence || a.type_id.localeCompare(b.type_id));

    let primary = scores.filter((score) => score.confidence >= 0.42).map((score) => score.type_id);
    let secondary = scores.filter((score) => score.confidence >= 0.28 && score.confidence < 0.42).map((score) => score.type_id);
    if (!primary.length) {
      primary = ["unknown_agent"];
      secondary = scores.filter((score) => score.confidence >= 0.1).map((score) => score.type_id).slice(0, 3);
    }
    const confidenceByType = {};
    scores.forEach((score) => {
      if (score.confidence >= 0.1) {
        confidenceByType[score.type_id] = round(score.confidence);
      }
    });
    if (primary.includes("unknown_agent")) {
      confidenceByType.unknown_agent = Object.keys(confidenceByType).length ? 0.58 : 0.82;
    }
    const matchedSignals = {};
    scores.forEach((score) => {
      if (score.signals.length) {
        matchedSignals[score.type_id] = score.signals;
      }
    });
    const riskFlags = riskFlagsFor(profile, primary.concat(secondary));
    return {
      primary_types: primary,
      secondary_types: secondary,
      rejected_types: [],
      confidence_by_type: confidenceByType,
      matched_signals: matchedSignals,
      negative_signals: {},
      risk_flags: riskFlags,
      missing_evidence: [],
      explanation: primary.includes("unknown_agent")
        ? "Insufficient non-name evidence for a concrete primary type."
        : "Classification uses declared, tool, task, permission, and policy signals; agent name is not scored."
    };
  }

  function profileFlagSignals(profile, typeId) {
    const flags = [];
    if (typeId === "coding_agent") {
      if (profile.can_write_files) flags.push({ value: "can_write_files", confidence: 0.1 });
      if (profile.can_run_code) flags.push({ value: "can_run_code", confidence: 0.12 });
      if (profile.can_read_files) flags.push({ value: "can_read_files", confidence: 0.05 });
    }
    if (typeId === "file_reading_agent" && profile.can_read_files) {
      flags.push({ value: "can_read_files", confidence: 0.17 });
    }
    if (typeId === "browser_navigation_agent") {
      if (profile.can_use_browser) flags.push({ value: "can_use_browser", confidence: 0.18 });
      if (profile.can_use_network) flags.push({ value: "can_use_network", confidence: 0.05 });
    }
    if (typeId === "financial_transaction_agent_simulated") {
      if (profile.can_execute_transactions) flags.push({ value: "can_execute_transactions", confidence: 0.22 });
      if (profile.requires_human_approval) flags.push({ value: "requires_human_approval", confidence: 0.05 });
    }
    if (typeId === "general_tool_use_agent" && profile.tools.length) {
      flags.push({ value: "tools_present", confidence: 0.22 });
    }
    if (typeId === "research_agent" && profile.can_use_network) {
      flags.push({ value: "can_use_network", confidence: 0.07 });
    }
    return flags;
  }

  function selectCategories(classification) {
    const types = classification.primary_types.concat(classification.secondary_types);
    if (classification.primary_types.includes("unknown_agent")) {
      types.push("unknown_agent");
    }
    const selected = state.categories.filter((category) => {
      const applicable = category.applicable_agent_types || [];
      return applicable.some((typeId) => types.includes(typeId));
    });
    return selected.length ? selected : state.categories.filter((category) => category.category_id === "profile_completion");
  }

  function resolveSources(classification, experiment) {
    const types = classification.primary_types.concat(classification.secondary_types);
    const sources = [
      {
        source_id: "profile_declared_capabilities",
        source_type: "user_declared",
        title: "User-entered description and declared capabilities",
        reliability: 0.25,
        limitations: ["Declared capability is weak evidence."]
      },
      {
        source_id: "profile_tool_task_inference",
        source_type: "inferred_from_tools",
        title: "Inferred from supplied tools, permissions, and sample tasks",
        reliability: 0.55,
        limitations: ["Tool/task inference needs observed traces."]
      }
    ];
    if (experiment) {
      sources.push({
        source_id: "pasted_experiment_summary",
        source_type: experiment.evidence_source,
        title: "Pasted experiment or trace summary",
        reliability: experiment.evidence_source === "imported_trace" ? 0.8 : 0.95,
        limitations: experiment.limitations || []
      });
    }
    state.sources.forEach((source) => {
      const applies = source.applies_to || [];
      if (applies.includes("evaluation_methodology") || applies.some((typeId) => types.includes(typeId))) {
        sources.push(Object.assign({}, source, {
          reliability: Math.min(Number(source.reliability || 0.2), 0.2),
          limitations: (source.limitations || []).concat(["Contextual reference only; not a direct score."])
        }));
      }
    });
    return sources;
  }

  function missingEvidence(profile, classification, categories, experiment, sources) {
    const missing = [];
    if (!profile.tools.length) missing.push("Tool surface is missing.");
    if (!profile.sample_tasks.length) missing.push("Representative sample tasks are missing.");
    if (!profile.declared_capabilities.length && !profile.description.trim()) missing.push("Declared capability or description is missing.");
    if (profile.autonomy_level === "unknown") missing.push("Autonomy level is unknown.");
    if (classification.primary_types.includes("unknown_agent")) missing.push("Insufficient evidence for a non-unknown primary classification.");
    if (!experiment) missing.push("No observed experiment summary or imported trace is linked to this agent.");
    categories.forEach((category) => {
      if (!experiment || experiment.eval_category !== category.category_id) {
        missing.push(`No experiment summary for eval category: ${category.category_id}.`);
      }
    });
    if (sources.some((source) => source.source_type === "benchmark_reference") && !experiment) {
      missing.push("Benchmark references are contextual only; no comparable run is present.");
    }
    return Array.from(new Set(missing)).sort();
  }

  function scoreProfile(profile, classification, experiment, missing, sources) {
    const typedConfidences = Object.entries(classification.confidence_by_type)
      .filter(([typeId]) => typeId !== "unknown_agent")
      .map(([, value]) => Number(value));
    const evidenceStrength = experiment ? (experiment.evidence_source === "imported_trace" ? 0.8 : 0.9) : Math.min(0.6, average(sources.filter((source) => !/reference/.test(source.source_type)).map((source) => Number(source.reliability || 0))));
    const riskCount = classification.risk_flags.filter((flag) => /risk|external|network|filesystem|transaction|private/.test(flag)).length;
    const approvalRisky = classification.risk_flags.includes("high_risk_action_surface");
    const approvalScore = approvalRisky ? (profile.requires_human_approval ? 0.62 : 0.25) : 0.76;
    const scores = [
      score("capability_fit", typedConfidences.length ? Math.max.apply(null, typedConfidences) : 0.08, 0.35, "Fit between non-name signals and broad agent types."),
      score("evidence_strength", evidenceStrength, experiment ? 0.8 : 0.3, "Observed or imported evidence improves confidence; references do not score performance."),
      score("tool_risk", Math.max(0, 1 - riskCount * 0.14), 0.55, "Higher side-effect tools lower this safety-oriented score."),
      score("autonomy_risk", profile.autonomy_level === "high" ? 0.55 : 0.78, 0.45, "High autonomy increases risk unless constrained by approval and traces."),
      score("task_clarity", profile.sample_tasks.length ? 0.75 : 0.25, profile.sample_tasks.length ? 0.55 : 0.25, "Specific sample tasks improve eval-category selection."),
      score("approval_safety", approvalScore, 0.5, "Human approval can reduce risk but does not prove competence."),
      score("data_access_risk", classification.risk_flags.includes("private_or_sensitive_data_access") ? 0.42 : 0.75, 0.45, "Sensitive data access requires boundary tests."),
      score("missing_evidence_penalty", Math.max(0, 1 - Math.min(0.75, missing.length * 0.06)), 0.65, "Missing evidence lowers prediction confidence.")
    ];
    const byDimension = Object.fromEntries(scores.map((item) => [item.dimension, item.score]));
    const expected = byDimension.capability_fit * 0.32 + byDimension.evidence_strength * 0.3 + byDimension.task_clarity * 0.14 + byDimension.approval_safety * 0.1 + byDimension.tool_risk * 0.08 + byDimension.missing_evidence_penalty * 0.06;
    scores.push(score("expected_reliability", expected, experiment ? 0.55 : 0.28, "Preliminary reliability estimate from fit, evidence, clarity, and risk."));
    return scores;
  }

  function predictOutcome(classification, scores, missing, experiment) {
    const byDimension = Object.fromEntries(scores.map((item) => [item.dimension, item.score]));
    const riskFlags = classification.risk_flags;
    if (classification.primary_types.includes("unknown_agent") && byDimension.expected_reliability < 0.35) {
      return {
        predicted_success: null,
        confidence: 0.05,
        likely_strengths: [],
        likely_failures: ["insufficient profile detail", "no observed experiment or trace evidence"],
        risk_flags: riskFlags,
        evidence_basis: ["unsupported claim: classification is unknown", "declared descriptions are not performance evidence"],
        assumptions: ["The agent may have capabilities that were not supplied."],
        missing_evidence: missing,
        recommended_next_tests: recommendedTests(classification, missing),
        explanation: "Insufficient evidence to predict performance."
      };
    }
    let penalty = 0;
    if (riskFlags.includes("high_risk_action_surface")) penalty += 0.08;
    if (riskFlags.includes("external_state_modification")) penalty += 0.05;
    if (riskFlags.includes("financial_transaction_simulation_only")) penalty += 0.08;
    const predicted = Math.max(0, Math.min(1, byDimension.expected_reliability - penalty));
    const confidence = Math.max(0.05, Math.min(0.85, average(scores.map((item) => item.confidence)) * 0.45 + byDimension.evidence_strength * 0.35 + (experiment ? 0.2 : 0)));
    return {
      predicted_success: round(predicted),
      confidence: round(confidence),
      likely_strengths: strengthsFor(byDimension, experiment),
      likely_failures: failuresFor(classification, missing),
      risk_flags: riskFlags,
      evidence_basis: [
        confidence < 0.55 ? "low-confidence estimate" : "evidence-backed preliminary estimate",
        "classification uses tool, permission, task, and policy signals rather than agent name",
        "benchmark and methodology references are contextual, not direct scores",
        experiment ? "pasted experiment summary increased confidence" : "no linked observed/imported experiment evidence is available"
      ],
      assumptions: ["Target tasks resemble the sample tasks.", "No hidden tools are added at runtime."],
      missing_evidence: missing,
      recommended_next_tests: recommendedTests(classification, missing),
      explanation: `${confidence < 0.35 ? "Low" : "Moderate"} confidence preliminary success estimate; replace with observed eval results before deployment.`
    };
  }

  function riskFlagsFor(profile, typeIds) {
    const flags = [];
    if (profile.can_write_files || profile.can_run_code) flags.push("filesystem_or_code_execution");
    if (profile.can_use_browser || profile.can_use_network) flags.push("network_or_browser_access");
    if (profile.can_modify_external_state) flags.push("external_state_modification");
    if (profile.can_execute_transactions) flags.push("transaction_like_action_surface", "high_risk_action_surface");
    if (profile.requires_human_approval) flags.push("human_approval_required");
    if (profile.autonomy_level === "high") flags.push("high_autonomy");
    if (typeIds.includes("financial_transaction_agent_simulated")) flags.push("financial_transaction_simulation_only", "explicit_approval_required", "high_risk_action_surface");
    return Array.from(new Set(flags)).sort();
  }

  function inferredCapabilities(classification) {
    const capabilities = [];
    Object.values(classification.matched_signals).forEach((signals) => {
      signals.forEach((item) => capabilities.push(item.matched_value));
    });
    return Array.from(new Set(capabilities)).sort();
  }

  function recommendedTests(classification) {
    const tests = [];
    const types = classification.primary_types.concat(classification.secondary_types);
    state.categories.forEach((category) => {
      if ((category.applicable_agent_types || []).some((typeId) => types.includes(typeId))) {
        tests.push(category.category_id);
      }
    });
    if (classification.primary_types.includes("unknown_agent")) tests.push("complete_agent_profile");
    if (classification.risk_flags.includes("financial_transaction_simulation_only")) tests.push("run_simulated_authorization_and_refusal_tests");
    tests.push("record_minimal_trace_or_experiment_summary");
    return Array.from(new Set(tests)).sort();
  }

  function strengthsFor(scores, experiment) {
    const strengths = [];
    if (scores.capability_fit >= 0.55) strengths.push("profile signals fit broad agent categories");
    if (scores.task_clarity >= 0.7) strengths.push("sample tasks are specific enough to pick eval categories");
    if (experiment) strengths.push("pasted experiment summary provides direct evidence");
    return strengths;
  }

  function failuresFor(classification, missing) {
    const failures = [];
    if (missing.length) failures.push("missing evidence may hide important failure modes");
    if (classification.risk_flags.includes("network_or_browser_access")) failures.push("web or browser state may differ from declared tasks");
    if (classification.risk_flags.includes("filesystem_or_code_execution")) failures.push("code or filesystem changes may regress without tests");
    if (classification.risk_flags.includes("financial_transaction_simulation_only")) failures.push("transaction workflow must remain simulated and approval-gated");
    return Array.from(new Set(failures)).sort();
  }

  function renderReport(report) {
    const output = document.getElementById("agent-eval-output");
    output.innerHTML = [
      section("Classified agent type(s)", chips(report.classification.primary_types.concat(report.classification.secondary_types))),
      section("Inferred capabilities", list(report.inferred_capabilities)),
      section("Matched signals", matchedSignals(report.classification.matched_signals)),
      section("Risk flags", chips(report.classification.risk_flags, "risk")),
      section("Applicable eval categories", list(report.applicable_eval_categories.map((category) => `${category.category_id}: ${category.label}`))),
      section("Preliminary scorecard", scoreHtml(report.preliminary_scores)),
      section("Outcome prediction", predictionHtml(report.outcome_prediction)),
      section("Evidence basis", list(report.outcome_prediction.evidence_basis)),
      section("Data/source references used", list(report.evidence_summary.map(sourceSummary))),
      section("Missing evidence", list(report.missing_evidence)),
      section("Recommended next evals", list(report.outcome_prediction.recommended_next_tests))
    ].join("");
    document.getElementById("json-export").value = JSON.stringify(report, null, 2);
    document.getElementById("markdown-export").value = markdownReport(report);
  }

  function markdownReport(report) {
    const prediction = report.outcome_prediction.predicted_success === null ? "unsupported" : report.outcome_prediction.predicted_success;
    const matchedSignalLines = markdownMatchedSignals(report.classification.matched_signals);
    return [
      "# Agent Evaluation Report",
      "",
      "## Classified Agent Types",
      `- Primary: ${report.classification.primary_types.join(", ")}`,
      `- Secondary: ${report.classification.secondary_types.join(", ") || "none"}`,
      "",
      "## Matched Signals",
      ...matchedSignalLines,
      "",
      "## Evidence Basis",
      ...report.outcome_prediction.evidence_basis.map((item) => `- ${item}`),
      "",
      "## Data/Source References",
      ...report.evidence_summary.map((source) => `- ${sourceSummary(source)}`),
      "",
      "## Outcome Prediction",
      `- Predicted success: ${prediction}`,
      `- Prediction confidence: ${report.outcome_prediction.confidence}`,
      "",
      "## Missing Evidence",
      ...report.missing_evidence.map((item) => `- ${item}`),
      "",
      "## Recommended Next Evals",
      ...report.outcome_prediction.recommended_next_tests.map((item) => `- ${item}`),
      "",
      "## Limitations",
      ...report.limitations.map((item) => `- ${item}`)
    ].join("\n");
  }

  function markdownMatchedSignals(signalsByType) {
    const lines = [];
    Object.entries(signalsByType || {}).forEach(([typeId, signals]) => {
      signals.forEach((signalItem) => {
        lines.push(`- ${typeId}: ${signalItem.source_field} -> ${signalItem.matched_value} (confidence ${signalItem.confidence})`);
      });
    });
    return lines.length ? lines : ["- none"];
  }

  function section(title, body) {
    return `<div class="ae-section"><h3>${escapeHtml(title)}</h3>${body}</div>`;
  }

  function list(items) {
    if (!items || !items.length) return "<p>No items.</p>";
    return `<ul class="ae-list">${items.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}</ul>`;
  }

  function chips(items, extraClass) {
    if (!items || !items.length) return "<p>No items.</p>";
    return `<div class="ae-chip-row">${items.map((item) => `<span class="ae-chip ${extraClass || ""}">${escapeHtml(String(item))}</span>`).join("")}</div>`;
  }

  function matchedSignals(signalsByType) {
    const rows = [];
    Object.entries(signalsByType || {}).forEach(([typeId, signals]) => {
      rows.push(`${typeId}: ${signals.map((signalItem) => `${signalItem.source_field}:${signalItem.matched_value}`).join(", ")}`);
    });
    return list(rows);
  }

  function scoreHtml(scores) {
    return scores.map((item) => `<div class="ae-score"><strong>${escapeHtml(item.dimension)}</strong><div><div class="ae-bar"><span style="width:${Math.round(item.score * 100)}%"></span></div><small>score ${item.score}, confidence ${item.confidence}</small></div></div>`).join("");
  }

  function predictionHtml(prediction) {
    const success = prediction.predicted_success === null ? "unsupported" : prediction.predicted_success;
    return `<p><strong>Predicted success:</strong> ${escapeHtml(String(success))}</p><p><strong>Prediction confidence:</strong> ${escapeHtml(String(prediction.confidence))}</p><p>${escapeHtml(prediction.explanation)}</p>`;
  }

  function sourceSummary(source) {
    const url = source.url ? ` (${source.url})` : "";
    return `${source.source_id} [${source.source_type}, reliability=${Number(source.reliability || 0).toFixed(2)}]: ${source.title}${url}`;
  }

  function signal(typeId, kind, sourceField, value, strength, confidence) {
    return {
      signal_id: `${typeId}:${kind}:${value.replace(/[^a-z0-9]+/gi, "_").toLowerCase()}`,
      label: value,
      source_field: sourceField,
      matched_value: value,
      capability: value,
      strength,
      confidence,
      explanation: kind === "declared" ? "Declared capability is weak evidence." : "Signal supports broad capability inference."
    };
  }

  function score(dimension, value, confidence, explanation) {
    return { dimension, score: round(value), confidence: round(confidence), evidence_sources: [], missing_evidence: [], explanation };
  }

  function matchSignals(signals, text) {
    return signals.filter((signalText) => new RegExp(`(^|[^a-z0-9])${escapeRegExp(signalText).replace(/\\ /g, "\\s+")}([^a-z0-9]|$)`, "i").test(text));
  }

  function splitSentences(text) {
    return text.split(/[\n.]+/).map((item) => item.trim()).filter(Boolean);
  }

  function listFromText(text) {
    return text.split(/[,\n]+/).map((item) => item.trim()).filter(Boolean);
  }

  function normalize(values) {
    return values.filter(Boolean).join(" ").toLowerCase();
  }

  function average(values) {
    if (!values.length) return 0;
    return values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length;
  }

  function round(value) {
    return Math.round(Math.max(0, Math.min(1, Number(value || 0))) * 1000) / 1000;
  }

  function checked(id) {
    return document.getElementById(id).checked;
  }

  function valueOf(id) {
    return document.getElementById(id).value || "";
  }

  function setValue(id, value) {
    document.getElementById(id).value = value;
  }

  function setChecked(id, value) {
    document.getElementById(id).checked = Boolean(value);
  }

  function textField(value) {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    return value || "";
  }

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char]));
  }

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  window.Contract2AgentEvalDemo = {
    analyzeProfile,
    classifyProfile,
    scoreProfile,
    predictOutcome
  };
})();
