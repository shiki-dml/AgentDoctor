from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from contract2agent.evaluation.file_reading.compare import compare_with_references
from contract2agent.evaluation.file_reading.corpus import import_local_corpus, load_corpus_manifest
from contract2agent.evaluation.file_reading.graders import grade_run
from contract2agent.evaluation.file_reading.references import (
    curated_reference_sources,
    import_reference_source,
)
from contract2agent.evaluation.file_reading.reports import (
    write_profile_only_report,
    write_run_report,
)
from contract2agent.evaluation.file_reading.runner import run_file_reading_eval
from contract2agent.evaluation.file_reading.schema import to_dict
from contract2agent.evaluation.file_reading.tasks import (
    build_smoke_tasks,
    load_tasks_jsonl,
    validate_tasks,
    write_tasks_jsonl,
)


def register_typer_commands(root_app: Any, typer: Any, console: Any) -> None:
    file_eval = typer.Typer(help="CLI-driven file-reading agent evaluation.")

    @file_eval.command(name="import-local")
    def import_local_command(
        input_path: Path = typer.Option(..., "--input", help="Input file or directory."),
        out: Path = typer.Option(..., "--out", help="Output corpus directory."),
        manifest: Path | None = typer.Option(None, "--manifest", help="Manifest JSON path."),
        source_type: str = typer.Option("local", "--source-type", help="local, paper, reference, or methodology."),
        title: str = typer.Option("", "--title", help="Optional title for paper/reference imports."),
        include: list[str] | None = typer.Option(None, "--include", help="Include glob pattern; repeatable."),
        exclude: list[str] | None = typer.Option(None, "--exclude", help="Exclude glob pattern; repeatable."),
        license_name: str = typer.Option("", "--license", help="Source license metadata."),
    ) -> None:
        loaded = import_local_corpus(
            input_path,
            out,
            manifest,
            source_type=source_type,
            title=title,
            include_patterns=include,
            exclude_patterns=exclude,
            license_name=license_name,
        )
        console.print(f"Imported {len(loaded.documents)} document(s) into {out}")

    @file_eval.command(name="list-references")
    def list_references_command() -> None:
        console.print(json.dumps([to_dict(source) for source in curated_reference_sources()], indent=2, sort_keys=True))

    @file_eval.command(name="import-reference")
    def import_reference_command(
        source: str = typer.Option(..., "--source", help="Curated source id, such as qasper."),
        out: Path = typer.Option(..., "--out", help="Output metadata directory."),
        limit: int | None = typer.Option(None, "--limit", help="Optional source record limit."),
        allow_network: bool = typer.Option(False, "--allow-network", help="Required for network-enabled imports."),
    ) -> None:
        imported = import_reference_source(source, out, allow_network=allow_network, limit=limit)
        console.print(json.dumps(to_dict(imported), indent=2, sort_keys=True))

    @file_eval.command(name="validate")
    def validate_command(
        corpus: Path = typer.Option(..., "--corpus", help="Corpus manifest JSON."),
        tasks: Path = typer.Option(..., "--tasks", help="Task JSONL file."),
    ) -> None:
        errors = validate_tasks(corpus, tasks)
        if errors:
            for error in errors:
                console.print(f"Error: {error}")
            raise typer.Exit(1)
        console.print("Validation passed.")

    @file_eval.command(name="build-tasks")
    def build_tasks_command(
        corpus: Path = typer.Option(..., "--corpus", help="Corpus manifest JSON."),
        mode: str = typer.Option("smoke", "--mode", help="Task generation mode."),
        max_tasks: int = typer.Option(20, "--max-tasks", help="Maximum tasks to write."),
        out: Path = typer.Option(..., "--out", help="Output task JSONL path."),
        seed: int = typer.Option(0, "--seed", help="Deterministic seed."),
    ) -> None:
        manifest = load_corpus_manifest(corpus)
        tasks = build_smoke_tasks(manifest, max_tasks=max_tasks, seed=seed, mode=mode)
        write_tasks_jsonl(tasks, out)
        console.print(f"Wrote {len(tasks)} task(s) to {out}")

    @file_eval.command(name="run")
    def run_command(
        profile: Path = typer.Option(..., "--profile", help="FileReadingAgentProfile JSON."),
        agent_command: str = typer.Option(..., "--agent-command", help="Command with {input_json} and {output_json}."),
        corpus: Path = typer.Option(..., "--corpus", help="Corpus manifest JSON."),
        tasks: Path = typer.Option(..., "--tasks", help="Task JSONL file."),
        time_budget_seconds: float = typer.Option(60.0, "--time-budget-seconds", help="Total run time budget."),
        max_tasks: int | None = typer.Option(None, "--max-tasks", help="Maximum tasks to run."),
        seed: int = typer.Option(0, "--seed", help="Deterministic seed recorded in artifacts."),
        out: Path = typer.Option(..., "--out", help="Run output directory."),
    ) -> None:
        run = run_file_reading_eval(
            profile_path=profile,
            agent_command=agent_command,
            corpus_manifest_path=corpus,
            tasks_path=tasks,
            time_budget_seconds=time_budget_seconds,
            max_tasks=max_tasks,
            seed=seed,
            out_dir=out,
        )
        console.print(f"Wrote observed run {run.run_id} to {out}")

    @file_eval.command(name="profile-only")
    def profile_only_command(
        profile: Path = typer.Option(..., "--profile", help="FileReadingAgentProfile JSON."),
        out: Path = typer.Option(..., "--out", help="Report output directory."),
    ) -> None:
        paths = write_profile_only_report(profile, out)
        console.print(f"Wrote profile-only report to {paths['markdown']}")

    @file_eval.command(name="grade")
    def grade_command(
        run: Path = typer.Option(..., "--run", help="Run directory or run.json."),
        tasks: Path | None = typer.Option(None, "--tasks", help="Task JSONL file."),
        out: Path = typer.Option(..., "--out", help="Grade JSON path."),
    ) -> None:
        grades, scorecard = grade_run(run, tasks, out=out)
        console.print(f"Wrote {len(grades)} grade(s) to {out}; overall={scorecard.overall_score}")

    @file_eval.command(name="compare")
    def compare_command(
        run: Path = typer.Option(..., "--run", help="Run directory."),
        reference: Path = typer.Option(..., "--reference", help="Reference results JSON."),
        out: Path = typer.Option(..., "--out", help="Comparison Markdown or JSON path."),
    ) -> None:
        report = compare_with_references(run, reference, out=out)
        console.print(f"Wrote comparison to {out}; comparable={report.comparable}")

    @file_eval.command(name="report")
    def report_command(
        run: Path = typer.Option(..., "--run", help="Run directory."),
        report_format: str = typer.Option("md,json", "--format", help="md,json, markdown, or json."),
        out: Path = typer.Option(..., "--out", help="Report output directory."),
        reference: Path | None = typer.Option(None, "--reference", help="Optional reference results JSON."),
    ) -> None:
        paths = write_run_report(run, report_format=report_format, out_dir=out, reference_results=reference)
        console.print(f"Wrote report artifact(s): {', '.join(str(path) for path in paths.values())}")

    root_app.add_typer(file_eval, name="file-eval")


def add_file_eval_argparse(subparsers: argparse._SubParsersAction[Any]) -> None:
    parser = subparsers.add_parser("file-eval", help="CLI-driven file-reading agent evaluation.")
    sub = parser.add_subparsers(dest="file_eval_command", required=True)

    import_local = sub.add_parser("import-local")
    import_local.add_argument("--input", required=True, type=Path)
    import_local.add_argument("--out", required=True, type=Path)
    import_local.add_argument("--manifest", type=Path)
    import_local.add_argument("--source-type", default="local")
    import_local.add_argument("--title", default="")
    import_local.add_argument("--include", action="append")
    import_local.add_argument("--exclude", action="append")
    import_local.add_argument("--license", default="", dest="license_name")
    import_local.set_defaults(func=_argparse_import_local)

    list_refs = sub.add_parser("list-references")
    list_refs.set_defaults(func=_argparse_list_references)

    import_ref = sub.add_parser("import-reference")
    import_ref.add_argument("--source", required=True)
    import_ref.add_argument("--out", required=True, type=Path)
    import_ref.add_argument("--limit", type=int)
    import_ref.add_argument("--allow-network", action="store_true")
    import_ref.set_defaults(func=_argparse_import_reference)

    validate = sub.add_parser("validate")
    validate.add_argument("--corpus", required=True, type=Path)
    validate.add_argument("--tasks", required=True, type=Path)
    validate.set_defaults(func=_argparse_validate)

    build_tasks = sub.add_parser("build-tasks")
    build_tasks.add_argument("--corpus", required=True, type=Path)
    build_tasks.add_argument("--mode", default="smoke")
    build_tasks.add_argument("--max-tasks", type=int, default=20)
    build_tasks.add_argument("--out", required=True, type=Path)
    build_tasks.add_argument("--seed", type=int, default=0)
    build_tasks.set_defaults(func=_argparse_build_tasks)

    run = sub.add_parser("run")
    run.add_argument("--profile", required=True, type=Path)
    run.add_argument("--agent-command", required=True)
    run.add_argument("--corpus", required=True, type=Path)
    run.add_argument("--tasks", required=True, type=Path)
    run.add_argument("--time-budget-seconds", type=float, default=60.0)
    run.add_argument("--max-tasks", type=int)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--out", required=True, type=Path)
    run.set_defaults(func=_argparse_run)

    profile_only = sub.add_parser("profile-only")
    profile_only.add_argument("--profile", required=True, type=Path)
    profile_only.add_argument("--out", required=True, type=Path)
    profile_only.set_defaults(func=_argparse_profile_only)

    grade = sub.add_parser("grade")
    grade.add_argument("--run", required=True, type=Path)
    grade.add_argument("--tasks", type=Path)
    grade.add_argument("--out", required=True, type=Path)
    grade.set_defaults(func=_argparse_grade)

    compare = sub.add_parser("compare")
    compare.add_argument("--run", required=True, type=Path)
    compare.add_argument("--reference", required=True, type=Path)
    compare.add_argument("--out", required=True, type=Path)
    compare.set_defaults(func=_argparse_compare)

    report = sub.add_parser("report")
    report.add_argument("--run", required=True, type=Path)
    report.add_argument("--format", default="md,json")
    report.add_argument("--out", required=True, type=Path)
    report.add_argument("--reference", type=Path)
    report.set_defaults(func=_argparse_report)


def run_argparse_command(args: argparse.Namespace) -> int:
    return int(args.func(args) or 0)


def _argparse_import_local(args: argparse.Namespace) -> int:
    manifest = import_local_corpus(
        args.input,
        args.out,
        args.manifest,
        source_type=args.source_type,
        title=args.title,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        license_name=args.license_name,
    )
    print(f"Imported {len(manifest.documents)} document(s) into {args.out}")
    return 0


def _argparse_list_references(_args: argparse.Namespace) -> int:
    print(json.dumps([to_dict(source) for source in curated_reference_sources()], indent=2, sort_keys=True))
    return 0


def _argparse_import_reference(args: argparse.Namespace) -> int:
    imported = import_reference_source(args.source, args.out, allow_network=args.allow_network, limit=args.limit)
    print(json.dumps(to_dict(imported), indent=2, sort_keys=True))
    return 0


def _argparse_validate(args: argparse.Namespace) -> int:
    errors = validate_tasks(args.corpus, args.tasks)
    if errors:
        for error in errors:
            print(f"Error: {error}")
        return 1
    print("Validation passed.")
    return 0


def _argparse_build_tasks(args: argparse.Namespace) -> int:
    manifest = load_corpus_manifest(args.corpus)
    tasks = build_smoke_tasks(manifest, max_tasks=args.max_tasks, seed=args.seed, mode=args.mode)
    write_tasks_jsonl(tasks, args.out)
    print(f"Wrote {len(tasks)} task(s) to {args.out}")
    return 0


def _argparse_run(args: argparse.Namespace) -> int:
    run = run_file_reading_eval(
        profile_path=args.profile,
        agent_command=args.agent_command,
        corpus_manifest_path=args.corpus,
        tasks_path=args.tasks,
        time_budget_seconds=args.time_budget_seconds,
        max_tasks=args.max_tasks,
        seed=args.seed,
        out_dir=args.out,
    )
    print(f"Wrote observed run {run.run_id} to {args.out}")
    return 0


def _argparse_profile_only(args: argparse.Namespace) -> int:
    paths = write_profile_only_report(args.profile, args.out)
    print(f"Wrote profile-only report to {paths['markdown']}")
    return 0


def _argparse_grade(args: argparse.Namespace) -> int:
    grades, scorecard = grade_run(args.run, args.tasks, out=args.out)
    print(f"Wrote {len(grades)} grade(s) to {args.out}; overall={scorecard.overall_score}")
    return 0


def _argparse_compare(args: argparse.Namespace) -> int:
    report = compare_with_references(args.run, args.reference, out=args.out)
    print(f"Wrote comparison to {args.out}; comparable={report.comparable}")
    return 0


def _argparse_report(args: argparse.Namespace) -> int:
    paths = write_run_report(args.run, report_format=args.format, out_dir=args.out, reference_results=args.reference)
    print(f"Wrote report artifact(s): {', '.join(str(path) for path in paths.values())}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m contract2agent.evaluation.file_reading.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_file_eval_argparse(subparsers)
    args = parser.parse_args(argv)
    return run_argparse_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
