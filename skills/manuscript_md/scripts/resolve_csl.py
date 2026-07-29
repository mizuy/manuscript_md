#!/usr/bin/env python3
"""Resolve a CSL file for pandoc citeproc.

Search order:
  1. Absolute path (if the file exists)
  2. <paper-dir>/<name>
  3. <project-dir>/csl/<name>  (skill root: skills/manuscript_md)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_csl(name: str, *, paper_dir: Path, project_dir: Path | None = None) -> Path:
    project_dir = project_dir or project_root()
    raw = Path(name).expanduser()
    if raw.is_absolute():
        if raw.is_file():
            return raw.resolve()
        raise FileNotFoundError(f"CSL not found: {raw}")

    basename = raw.name
    for candidate in (paper_dir / basename, project_dir / "csl" / basename, paper_dir / raw):
        if candidate.is_file():
            return candidate.resolve()

    available = sorted(p.name for p in (project_dir / "csl").glob("*.csl"))
    hint = ", ".join(available) if available else "(none)"
    raise FileNotFoundError(
        f"CSL not found: {name}\n"
        f"  paper-dir: {paper_dir.resolve()}\n"
        f"  project csl/: {project_dir / 'csl'}\n"
        f"  available: {hint}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csl",
        nargs="?",
        default="vancouver.csl",
        help="CSL file name or absolute path (default: vancouver.csl)",
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=Path.cwd(),
        help="Paper directory (default: cwd)",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Project root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List bundled CSL files and exit",
    )
    args = parser.parse_args()
    project_dir = args.project_dir or project_root()

    if args.list:
        for path in sorted((project_dir / "csl").glob("*.csl")):
            print(path.name)
        return

    try:
        print(resolve_csl(args.csl, paper_dir=args.paper_dir, project_dir=project_dir))
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
