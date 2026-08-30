"""Resolve pandoc --reference-doc."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from manuscript_md.paths import SKILL_MD


def resolve_reference_doc(
    name: str,
    *,
    paper_dir: Path,
    project_dir: Path | None = None,
) -> Path:
    project_dir = project_dir or SKILL_MD
    raw = Path(name).expanduser()
    if raw.is_absolute():
        if raw.is_file():
            return raw.resolve()
        raise FileNotFoundError(f"reference-doc not found: {raw}")

    basename = raw.name
    for candidate in (
        paper_dir / basename,
        paper_dir / raw,
        project_dir / "templates" / basename,
    ):
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        f"reference-doc not found: {name}\n"
        f"  paper-dir: {paper_dir.resolve()}\n"
        f"  skill templates/: {project_dir / 'templates'}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "name",
        nargs="?",
        default="reference.docx",
        help="Docx name or absolute path (default: reference.docx)",
    )
    parser.add_argument("--paper-dir", type=Path, default=Path.cwd())
    parser.add_argument("--project-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        path = resolve_reference_doc(
            args.name,
            paper_dir=args.paper_dir,
            project_dir=args.project_dir,
        )
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(path)
    return 0
