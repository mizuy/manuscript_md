#!/usr/bin/env python3
"""Expand ``@import "path"`` lines before pandoc.

``@import`` is an endolab ``analysis_report.md`` convention; pandoc does not
understand it. ``task paper:docx`` runs this script first.

Paths in ``@import`` are resolved relative to the file that contains the line.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

IMPORT_RE = re.compile(r'^@import\s+"([^"]+)"\s*$')
_EM_SPACE = "\u2003"
_TABLE_SEP_RE = re.compile(r"^\|[\s\-:]+\|")


def _leading_spaces_to_em(cell: str) -> str:
    # GFM pipe cells have a single padding space after ``|``; only ``  ``+ is nested indent.
    match = re.match(r"^(  +)(.*)$", cell)
    if not match:
        return cell
    level = len(match.group(1)) // 2
    return _EM_SPACE * level + match.group(2).lstrip()


def normalize_table_cell_indents(text: str) -> str:
    """Convert leading ASCII spaces in the first table column to em spaces.

    Pandoc removes leading spaces when parsing GFM pipe tables; em spaces are kept
    and render nested indication rows correctly in Word.
    """
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("|"):
            out.append(line)
            continue
        if _TABLE_SEP_RE.match(stripped):
            out.append(line)
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            first = parts[1]
            converted = _leading_spaces_to_em(first)
            if converted != first:
                parts[1] = converted
                line = "|".join(parts)
        out.append(line)
    return "\n".join(out)


def expand_markdown(text: str, base_dir: Path, *, _stack: tuple[Path, ...] = ()) -> str:
    out_lines: list[str] = []
    for line in text.splitlines():
        match = IMPORT_RE.match(line)
        if not match:
            out_lines.append(line)
            continue
        rel = match.group(1)
        target = (base_dir / rel).resolve()
        if not target.is_file():
            raise FileNotFoundError(f"@import target not found: {rel} (from {base_dir})")
        if target in _stack:
            chain = " -> ".join(str(p) for p in (*_stack, target))
            raise ValueError(f"circular @import: {chain}")
        fragment = target.read_text(encoding="utf-8")
        expanded = expand_markdown(fragment, target.parent, _stack=(*_stack, target))
        if out_lines and out_lines[-1] != "":
            out_lines.append("")
        out_lines.extend(expanded.splitlines())
        out_lines.append("")
    return "\n".join(out_lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source markdown (e.g. manuscript.md)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Expanded markdown for pandoc",
    )
    args = parser.parse_args()
    src = args.input.resolve()
    if not src.is_file():
        print(f"error: input not found: {src}", file=sys.stderr)
        return 1
    expanded = expand_markdown(src.read_text(encoding="utf-8"), src.parent)
    expanded = normalize_table_cell_indents(expanded)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expanded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
