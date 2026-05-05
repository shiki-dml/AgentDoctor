from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from contract2agent.evaluation.file_reading.corpus import load_corpus_manifest
from contract2agent.evaluation.file_reading.graders import validate_target_output
from contract2agent.evaluation.file_reading.schema import (
    FileAccessTrace,
    FileReadingAgentProfile,
    FileReadingRun,
    TargetAgentInput,
    TargetAgentOutput,
    from_dict,
    to_dict,
)
from contract2agent.evaluation.file_reading.tasks import load_tasks_jsonl


REQUIRED_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["answer", "citations"],
    "properties": {
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["file_id", "line_start", "line_end", "quote"],
            },
        },
        "confidence": {"type": "number"},
        "files_read": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
}


def run_file_reading_eval(
    *,
    profile_path: str | Path,
    agent_command: str,
    corpus_manifest_path: str | Path,
    tasks_path: str | Path,
    time_budget_seconds: float,
    max_tasks: int | None,
    seed: int,
    out_dir: str | Path,
) -> FileReadingRun:
    if "{input_json}" not in agent_command or "{output_json}" not in agent_command:
        raise ValueError("--agent-command must include {input_json} and {output_json} placeholders")
    profile = load_file_reading_agent_profile(profile_path)
    manifest = load_corpus_manifest(corpus_manifest_path)
    tasks = load_tasks_jsonl(tasks_path)
    selected_tasks = tasks[: max_tasks if max_tasks is not None else len(tasks)]
    run_root = Path(out_dir)
    run_root.mkdir(parents=True, exist_ok=True)
    for child in ("inputs", "outputs", "stdout", "stderr"):
        (run_root / child).mkdir(parents=True, exist_ok=True)

    run_id = f"file-reading-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    started_at = datetime.now(timezone.utc).isoformat()
    deadline = time.monotonic() + max(0.0, time_budget_seconds)
    outputs: dict[str, TargetAgentOutput] = {}
    traces: dict[str, FileAccessTrace] = {}
    completed_tasks = []
    status = "completed"

    for task in selected_tasks:
        remaining = deadline - time.monotonic()
        if time_budget_seconds > 0 and remaining <= 0:
            status = "time_budget_exhausted"
            break
        input_path = run_root / "inputs" / f"{task.task_id}.json"
        output_path = run_root / "outputs" / f"{task.task_id}.json"
        stdout_path = run_root / "stdout" / f"{task.task_id}.txt"
        stderr_path = run_root / "stderr" / f"{task.task_id}.txt"
        agent_input = TargetAgentInput(
            task_id=task.task_id,
            question=task.question,
            corpus_dir=manifest.root_path,
            manifest_path=str(Path(corpus_manifest_path)),
            allowed_files=task.allowed_files or manifest.allowed_files,
            forbidden_files=task.forbidden_files or manifest.forbidden_files,
            instructions=task.instructions,
            required_output_schema=REQUIRED_OUTPUT_SCHEMA,
            metadata={
                "task_type": task.task_type,
                "negative_checks": task.negative_checks,
            },
        )
        input_path.write_text(
            json.dumps(to_dict(agent_input), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        command = _command_args(agent_command, input_path, output_path)
        start_time = datetime.now(timezone.utc)
        start_monotonic = time.monotonic()
        timeout_seconds = max(0.001, remaining if time_budget_seconds > 0 else 24 * 60 * 60)
        timeout = False
        exit_code: int | None = None
        stdout_text = ""
        stderr_text = ""
        try:
            completed = subprocess.run(
                command,
                cwd=run_root,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                shell=False,
            )
            exit_code = completed.returncode
            stdout_text = completed.stdout
            stderr_text = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timeout = True
            status = "completed_with_task_failures"
            stdout_text = _decode_timeout_stream(exc.stdout)
            stderr_text = _decode_timeout_stream(exc.stderr)
        except OSError as exc:
            status = "completed_with_task_failures"
            exit_code = None
            stderr_text = f"{type(exc).__name__}: {exc}"
        end_time = datetime.now(timezone.utc)
        duration = time.monotonic() - start_monotonic
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        output = _load_agent_output(output_path)
        forbidden_touched = sorted(
            set(output.files_read).intersection(set(agent_input.forbidden_files))
        )
        trace = FileAccessTrace(
            task_id=task.task_id,
            files_read=output.files_read,
            files_referenced=sorted(
                {citation.file_id for citation in output.citations if citation.file_id}
            ),
            forbidden_files_touched=forbidden_touched,
            stdout_path=_relative(run_root, stdout_path),
            stderr_path=_relative(run_root, stderr_path),
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=round(duration, 6),
            timeout=timeout,
            command=command,
            exit_code=exit_code,
            metadata={"output_path": _relative(run_root, output_path)},
        )
        outputs[task.task_id] = output
        traces[task.task_id] = trace
        completed_tasks.append(task)
        if timeout and time_budget_seconds > 0 and deadline - time.monotonic() <= 0:
            status = "time_budget_exhausted"
            break

    run = FileReadingRun(
        run_id=run_id,
        agent_profile=profile,
        corpus_manifest=manifest,
        task_file=str(tasks_path),
        tasks=completed_tasks,
        outputs=outputs,
        traces=traces,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc).isoformat(),
        time_budget_seconds=time_budget_seconds,
        max_tasks=max_tasks,
        seed=seed,
        status=status,
        metadata={
            "scoring_method": "contract2agent_file_reading_v1",
            "task_pack_id": Path(tasks_path).stem,
            "observed_run": True,
            "network_used": False,
        },
    )
    _write_run_artifacts(run, run_root)
    return run


def load_file_reading_agent_profile(path: str | Path) -> FileReadingAgentProfile:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"File reading agent profile must contain an object: {path}")
    return from_dict(FileReadingAgentProfile, data)


def _write_run_artifacts(run: FileReadingRun, run_root: Path) -> None:
    (run_root / "run.json").write_text(
        json.dumps(to_dict(run), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = []
    for task in run.tasks:
        lines.append(
            json.dumps(
                {
                    "task": to_dict(task),
                    "output": to_dict(run.outputs.get(task.task_id, TargetAgentOutput())),
                    "trace": to_dict(run.traces[task.task_id]),
                },
                sort_keys=True,
            )
        )
    (run_root / "run.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _load_agent_output(output_path: Path) -> TargetAgentOutput:
    try:
        raw_output = output_path.read_text(encoding="utf-8")
    except OSError as exc:
        return TargetAgentOutput(
            raw_output="",
            schema_valid=False,
            errors=[f"output file missing or unreadable: {type(exc).__name__}: {exc}"],
        )
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        return TargetAgentOutput(
            raw_output=raw_output,
            schema_valid=False,
            errors=[f"output JSON parse error at line {exc.lineno}: {exc.msg}"],
        )
    return validate_target_output(data, raw_output=raw_output)


def _command_args(agent_command: str, input_path: Path, output_path: Path) -> list[str]:
    parts = shlex.split(agent_command, posix=os.name != "nt")
    return [
        _strip_wrapping_quotes(part)
        .replace("{input_json}", str(input_path))
        .replace("{output_json}", str(output_path))
        for part in parts
    ]


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _decode_timeout_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name
