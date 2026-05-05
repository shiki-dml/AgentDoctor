from __future__ import annotations

import fnmatch
import hashlib
import json
import mimetypes
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from contract2agent.evaluation.file_reading.schema import (
    CorpusManifest,
    DocumentRecord,
    ReferenceSource,
    to_dict,
)


SUPPORTED_TEXT_EXTENSIONS = {
    ".c",
    ".cfg",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".hpp",
    ".htm",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".rs",
    ".rst",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

UNSAFE_DIR_NAMES = {
    ".cache",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "browser data",
    "coverage",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
}

UNSAFE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".envrc",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
    "known_hosts",
    "secrets.json",
}

SECRET_NAME_PATTERNS = [
    "*token*",
    "*secret*",
    "*password*",
    "*.key",
    "*.pem",
    "*.pfx",
    "*.sqlite",
    "*.sqlite3",
]


def import_local_corpus(
    input_path: str | Path,
    out_dir: str | Path,
    manifest_path: str | Path | None = None,
    *,
    source_type: str = "local",
    title: str = "",
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    license_name: str = "",
    provenance: str = "",
    limitations: list[str] | None = None,
) -> CorpusManifest:
    """Copy a safe text corpus into out_dir and write a manifest."""
    source = Path(input_path).resolve()
    target_root = Path(out_dir).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    target_root.mkdir(parents=True, exist_ok=True)
    manifest_target = (
        Path(manifest_path).resolve()
        if manifest_path is not None
        else target_root / "manifest.json"
    )

    include_patterns = include_patterns or ["*"]
    exclude_patterns = exclude_patterns or []
    skipped: list[str] = []
    documents: list[DocumentRecord] = []
    candidates = _candidate_files(source)
    for src in candidates:
        rel = _relative_to_source(src, source)
        rel_posix = rel.as_posix()
        if not _matches(rel_posix, include_patterns):
            skipped.append(f"{rel_posix}: not included by pattern")
            continue
        if _matches(rel_posix, exclude_patterns):
            skipped.append(f"{rel_posix}: excluded by pattern")
            continue
        unsafe_reason = unsafe_path_reason(src, rel)
        if unsafe_reason:
            skipped.append(f"{rel_posix}: {unsafe_reason}")
            continue
        if src.suffix.casefold() == ".pdf":
            skipped.append(
                f"{rel_posix}: PDF text extraction is not built in; convert to text/markdown "
                "or install a future optional PDF extra."
            )
            continue
        if src.suffix.casefold() not in SUPPORTED_TEXT_EXTENSIONS:
            skipped.append(f"{rel_posix}: unsupported extension")
            continue
        dest = target_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        record = document_record(dest, rel_posix, source_type=source_type)
        documents.append(record)

    allowed_files = [document.file_id for document in documents if document.allowed]
    forbidden_files = [document.file_id for document in documents if not document.allowed]
    corpus_hash = _manifest_hash(documents)
    created_at = datetime.now(timezone.utc).isoformat()
    manifest = CorpusManifest(
        corpus_id=_corpus_id(source, corpus_hash),
        root_path=str(target_root),
        documents=documents,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        source_type=source_type,
        created_at=created_at,
        hash=corpus_hash,
        metadata={
            "title": title,
            "skipped": skipped,
            "document_count": len(documents),
            "network_used": False,
        },
        provenance=provenance or f"Local import from {sanitize_absolute_path(source)}",
        license=license_name,
        limitations=limitations
        or [
            "Only supported text-like files are imported.",
            "Unsafe secret/cache paths are skipped by default.",
        ],
    )
    manifest_target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.write_text(
        json.dumps(to_dict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if source_type in {"paper", "reference", "methodology"}:
        reference = ReferenceSource(
            source_id=f"local_{source_type}_{corpus_hash[:12]}",
            title=title or source.name,
            source_type=source_type,
            domain="file_reading_agent",
            local_path=str(manifest_target),
            license=license_name,
            provenance=manifest.provenance,
            reliability=0.45,
            applicable_task_types=[],
            metrics_available=[],
            notes=[
                "User-provided local reference material imported without network access.",
                "This source is contextual unless linked to observed eval results.",
            ],
            limitations=manifest.limitations,
        )
        (target_root / "reference_source.json").write_text(
            json.dumps(to_dict(reference), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return manifest


def load_corpus_manifest(path: str | Path) -> CorpusManifest:
    from contract2agent.evaluation.file_reading.schema import from_dict

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Corpus manifest must contain an object: {path}")
    return from_dict(CorpusManifest, data)


def document_record(
    path: Path,
    relative_path: str,
    *,
    source_type: str = "local",
    allowed: bool = True,
) -> DocumentRecord:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    headings = _section_headings(lines, path.suffix.casefold())
    line_count = len(lines)
    return DocumentRecord(
        file_id=relative_path,
        relative_path=relative_path,
        absolute_path_sanitized=f"<corpus_root>/{relative_path}",
        file_type=path.suffix.casefold().lstrip(".") or "text",
        mime_type=mimetypes.guess_type(path.name)[0] or "text/plain",
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        line_count=line_count,
        section_headings=headings,
        chunk_count=max(1, (line_count + 199) // 200),
        allowed=allowed,
        tags=[],
        source=source_type,
        metadata={},
    )


def unsafe_path_reason(path: Path, relative_path: Path | None = None) -> str:
    parts = [part.casefold() for part in path.parts]
    if relative_path is not None:
        parts.extend(part.casefold() for part in relative_path.parts)
    if any(part in UNSAFE_DIR_NAMES for part in parts[:-1]):
        return "unsafe/cache directory skipped"
    name = path.name.casefold()
    if name in UNSAFE_FILE_NAMES:
        return "secret-like file skipped"
    if any(fnmatch.fnmatch(name, pattern) for pattern in SECRET_NAME_PATTERNS):
        return "secret-like filename skipped"
    return ""


def sanitize_absolute_path(path: str | Path) -> str:
    candidate = Path(path)
    return f"<local>/{candidate.name}" if candidate.name else "<local>"


def _candidate_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    candidates: list[Path] = []
    for path in sorted(source.rglob("*")):
        if path.is_file():
            candidates.append(path)
    return candidates


def _relative_to_source(path: Path, source: Path) -> Path:
    if source.is_file():
        return Path(source.name)
    return path.relative_to(source)


def _matches(relative_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relative_path, pattern) for pattern in patterns)


def _section_headings(lines: list[str], suffix: str) -> list[str]:
    headings: list[str] = []
    for line in lines:
        stripped = line.strip()
        if suffix in {".md", ".rst"} and stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                headings.append(heading)
        elif suffix in {".html", ".htm"}:
            for match in re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", stripped, flags=re.I):
                clean = re.sub(r"<[^>]+>", "", match).strip()
                if clean:
                    headings.append(clean)
    return headings[:50]


def _manifest_hash(documents: list[DocumentRecord]) -> str:
    digest = hashlib.sha256()
    for document in sorted(documents, key=lambda item: item.relative_path):
        digest.update(document.relative_path.encode("utf-8"))
        digest.update(document.sha256.encode("utf-8"))
    return digest.hexdigest()


def _corpus_id(source: Path, corpus_hash: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", source.stem or source.name).strip("-")
    return f"{safe_name or 'corpus'}-{corpus_hash[:12]}"
