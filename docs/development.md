# Development

This page covers local development, tests, documentation preview, link checking, and GitHub Pages deployment.

## Local Setup

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
```

The current package metadata is:

- distribution name: `agenttracedoctor`
- source package: `contract2agent`
- CLI entry points: `agentdoctor`, `c2a`

## Run Tests

```bash
python -m pytest
```

If using the project virtual environment on Windows:

```powershell
.venv_uv\Scripts\python.exe -m pytest
```

## Compile Source

```bash
python -m compileall -q contract2agent tests scripts
```

This catches syntax errors across the package, tests, and local scripts without creating report artifacts that should be committed.

## Preview Docs

```bash
python -m mkdocs serve
```

Then open the local URL printed by MkDocs, usually `http://127.0.0.1:8000/`.

## Build Docs

```bash
python -m mkdocs build
```

For a strict CI-style build:

```bash
python -m mkdocs build --strict
```

## Check Internal Links

The repository includes a lightweight Markdown link checker:

```bash
python scripts/check_docs_links.py
```

It scans:

- `README.md`
- `docs/*.md`
- `examples/**/*.md`

It verifies relative Markdown links point to existing files or directories. External links and anchors are ignored.

## Engineering Notes

- [2026-05-04 bug audit](audits/2026-05-04-bug-audit.md)

## GitHub Pages Setup

The workflow file is `.github/workflows/docs.yml`. It builds MkDocs Material documentation and deploys to GitHub Pages on pushes to `main` and on manual `workflow_dispatch`.

In GitHub, enable:

```text
Repository settings -> Pages -> Source -> GitHub Actions
```

The workflow installs docs dependencies with:

```bash
python -m pip install -e ".[docs]"
```

and builds with:

```bash
python -m mkdocs build --strict
```

## Notes for Contributors

- Read the repository root `AGENTS.md` before broad edits; it records repository-specific setup, cleanup, and safety rules.
- Keep CLI documentation aligned with `contract2agent/cli.py`.
- Do not document unimplemented flags as if they work.
- Keep sample reports clearly marked as examples.
- Keep patch-preview and auto-mode docs conservative about safety and confidence.
- Run `python scripts/check_docs_links.py` after editing docs links.
- Run `python -m compileall -q contract2agent tests scripts` before committing doc-adjacent maintenance changes.
- Run `python -m pytest` after changes that touch source behavior.

## Cleanup Rules

Do not commit generated output, caches, virtual environments, runtime `.agentdoctor/` data, local `.tmp/` audit output, or generated MkDocs `site/` output. Keep intentional fixtures under `examples/` or `tests/fixtures/`, and sanitize local absolute paths before adding audit or troubleshooting notes to the repository.
