#!/usr/bin/env python3
"""Resolve pandoc --reference-doc.

Search order:
  1. Absolute path (if the file exists)
  2. <paper-dir>/<name>          (optional paper-local override)
  3. <project-dir>/templates/<name>  (skill default: reference.docx)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_reference_doc(
    name: str,
    *,
    paper_dir: Path,
    project_dir: Path | None = None,
) -> Path:
    project_dir = project_dir or project_root()
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "name",
        nargs="?",
        default="reference.docx",
        help="Docx name or absolute path (default: reference.docx)",
    )
    parser.add_argument("--paper-dir", type=Path, default=Path.cwd())
    parser.add_argument("--project-dir", type=Path, default=None)
    args = parser.parse_args()
    path = resolve_reference_doc(
        args.name,
        paper_dir=args.paper_dir,
        project_dir=args.project_dir,
    )
    print(path)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
