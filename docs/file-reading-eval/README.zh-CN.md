# 文件阅读智能体评估

## 概览

Contract2Agent 的 `file_reading_agent` 子系统用于本地、可观察的文件阅读评估。它可以导入受控语料、加载或生成任务、通过命令适配器运行目标智能体、捕获运行产物、执行确定性评分、在显式请求时追加 LLM 评审、比较兼容参考结果，并生成 Markdown / JSON 报告。

## 为什么需要观察式评估

文件阅读能力声明不是性能证据。`profile-only` 报告只能说明准备度、风险和下一步评估计划；实际阅读性能必须来自运行产物、答案、引用、轨迹和评分结果。

## 确定性评分与可选 LLM 评审

确定性评分默认启用且不需要 API。它覆盖答案正确性、引用存在性、引用文本匹配、行号范围准确性、文件选择、禁用文件安全、不可回答问题的拒答、输出 schema、延迟和不受支持声明等维度。

LLM 评审是可选、显式启用、非确定性的补充层。它只适合语义等价、摘要忠实度、矛盾风险、证据支持和建议综合，不替代引用、禁用文件、schema、路径、哈希或超时等确定性检查。

## 常用命令

```bash
c2a file-eval help workflow
c2a file-eval help llm
c2a file-eval doctor
c2a file-eval import-local --input examples/file_reading_eval/corpus --out .runs/file-corpus --manifest .runs/file-corpus/manifest.json
c2a file-eval validate --corpus .runs/file-corpus/manifest.json --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl
c2a file-eval run --profile examples/file_reading_eval/profiles/good_file_reader.json --agent-command "python examples/file_reading_eval/agents/dummy_good_reader.py {input_json} {output_json}" --corpus .runs/file-corpus/manifest.json --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl --out .runs/file-run
c2a file-eval grade --run .runs/file-run --tasks examples/file_reading_eval/tasks/smoke_tasks.jsonl --out .runs/file-run/grades.json
c2a file-eval report --run .runs/file-run --format md,json --out .runs/file-report
```

## LLM 评审安全规则

- 默认不调用 API；只有 `c2a file-eval judge`、`c2a file-eval run --judge llm` 或命令式评审适配器会启用评审。
- OpenAI 兼容路径默认读取 `OPENAI_API_KEY`，也可在交互终端中用隐藏的会话内输入。
- API key 不写入报告、日志、缓存、浏览器代码或已提交文件。
- 预算控制包括 `--judge-only`、`--max-judge-tasks`、`--llm-max-input-chars`、`--llm-max-output-tokens`、`--evidence-snippet-limit`、`--cost-budget-usd`、`--dry-run-cost-estimate` 和评审缓存开关。
- 评审输入只包含任务、答案、引用片段、金标证据、确定性评分摘要和失败模式，不包含完整语料、禁用文件或未清理的本地绝对路径。

## 报告解释

报告会展示观察到的任务数、确定性分数表、引用质量、文件选择、禁用文件安全、拒答行为、超时、参考结果兼容性、可选 LLM 评审状态、建议、限制和轨迹产物位置。公共 benchmark 或论文引用只提供上下文，除非任务包、评分方法、环境和条件兼容，否则不会产生直接分数差异。

## 静态页面约束

GitHub Pages 仍然只是静态查看器和演示页面。它不运行文件阅读实验，不调用 LLM/API，不接收 API key，也不执行实时智能体命令。

## 限制

- 基线评分是确定性的，但不是完整人工语义审查。
- LLM 评审结果是非确定性的、依赖提供方的补充信息。
- PDF 提取和网络数据集导入不属于默认依赖路径。
- 参考结果只有在兼容条件明确时才可比较；否则只能作为上下文证据。
